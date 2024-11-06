from typing import List
import cloudinary
import cloudinary.uploader
import redis.asyncio as redis
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, models, schemas
from app.auth import SECRET_KEY, ALGORITHM, create_access_token, create_refresh_token, get_current_user, Hash, \
    authenticate_user
from app.database import get_db
from app.email import send_verification_email
from app.models import User
from app.schemas import config, UserInDB

# list of allowed origins for CORS
origins = ["http://localhost:3000"]

app = FastAPI()
hash_handler = Hash()
router = APIRouter(prefix="/users", tags=["users"])

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

# Cloudinary settings
cloudinary.config(
    cloud_name=config.CLOUDINARY_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET,
    secure=True)


@app.on_event("startup")
async def startup():
    # connection to Redis and initialization of FastAPI Limiter with Redis
    app.redis = await redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=0,
        encoding="utf-8",
        decode_responses=True)
    await FastAPILimiter.init(app.redis)


# Route for getting the home page
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Contact API!"}


# Register new user
@app.post("/register", response_model=schemas.UserInDB, status_code=status.HTTP_201_CREATED)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await crud.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    hashed_password = await hash_handler.get_password_hash(user.password)
    db_user = await crud.create_user(db, user.email, hashed_password)

    # Send verification email
    await send_verification_email(email=user.email, username=user.email.split("@")[0], host="http://localhost:8000")
    return db_user


# Login for getting access token
@app.post("/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = await create_access_token(data={"sub": user.email})
    refresh_token = await create_refresh_token(data={"sub": user.email})
    return schemas.Token(access_token=access_token, refresh_token=refresh_token)


# Create a new contact (for current user only)
@app.post("/contacts/", response_model=schemas.ContactInDB,
          dependencies=[Depends(RateLimiter(times=5, seconds=60))],
          description="No more than 5 requests per minute allowed")
async def create_contact(
        contact: schemas.ContactCreate,
        db: AsyncSession = Depends(get_db),
        current_user: models.User = Depends(get_current_user)):
    return await crud.create_contact(db=db, contact=contact, owner_id=current_user.id)


# Get all contacts of the current user
@app.get("/contacts/", response_model=List[schemas.ContactInDB])
async def read_contacts(
        db: AsyncSession = Depends(get_db),
        current_user: models.User = Depends(get_current_user)):
    return await crud.get_contacts(db=db, owner_id=current_user.id)


# Get contact by ID (for authenticated users only)
@app.get("/contacts/{contact_id}", response_model=schemas.ContactInDB)
async def read_contact(
        contact_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: models.User = Depends(get_current_user)):
    contact = await crud.get_contact(db=db, contact_id=contact_id, owner_id=current_user.id)
    if contact is None or contact.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found or access denied")
    return contact


# Update contact (only for current user)
@app.put("/contacts/{contact_id}", response_model=schemas.ContactInDB)
async def update_contact(
        contact_id: int,
        contact: schemas.ContactUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: models.User = Depends(get_current_user)):
    existing_contact = await crud.get_contact(db=db, contact_id=contact_id, owner_id=current_user.id)
    if existing_contact is None or existing_contact.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found or access denied")
    updated_contact = await crud.update_contact(db=db, contact_id=contact_id, contact=contact, owner_id=current_user.id)
    return updated_contact


# Delete contact (only for current user)
@app.delete("/contacts/{contact_id}", response_model=schemas.ContactInDB)
async def delete_contact(
        contact_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: models.User = Depends(get_current_user)):
    contact = await crud.get_contact(db, contact_id, owner_id=current_user.id)
    if contact is None or contact.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found or access denied")
    deleted_contact = await crud.delete_contact(db=db, contact_id=contact_id)
    return deleted_contact


# Search contacts by first name, last name, email or additional info (only for current user)
@app.get("/contacts/search/", response_model=List[schemas.ContactInDB])
async def search_contacts(
        query: str,
        db: AsyncSession = Depends(get_db),
        current_user: models.User = Depends(get_current_user)):
    return await crud.search_contacts(db=db, query=query, owner_id=current_user.id)


# Get list of contacts with upcoming birthdays for the next 7 days (only for current user)
@app.get("/contacts/birthdays/", response_model=List[schemas.ContactInDB])
async def get_upcoming_birthdays(
        db: AsyncSession = Depends(get_db),
        current_user: models.User = Depends(get_current_user)):
    return await crud.get_upcoming_birthdays(db=db, owner_id=current_user.id)


# Confirm email
@app.get("/auth/confirm_email/{token}")
async def confirm_email(token: str, db: AsyncSession = Depends(get_db)):
    try:
        # decode token to get email
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload["sub"]
        if email is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

        # Activate user
        user = await crud.get_user_by_email(db, email)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user.is_verified = True
        await db.commit()
        return {"message": "Email confirmed"}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")


# Upload avatar
@app.patch('/avatar', response_model=UserInDB)
async def update_avatar(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    # Upload avatar to Cloudinary
    result = cloudinary.uploader.upload(
        file.file,
        public_id=f'PD_REST_API_contacts/{current_user.email}',
        overwrite=True)
    avatar_url = result.get("secure_url")

    if not avatar_url:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload avatar")

    # Update avatar in the database
    updated_user = await crud.update_avatar(db=db, email=current_user.email, avatar_url=avatar_url)
    return updated_user
