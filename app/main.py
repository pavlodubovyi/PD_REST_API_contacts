import os
from typing import List
import cloudinary
import cloudinary.uploader
import redis.asyncio as redis
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter, UploadFile, File, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse

from app import crud, models, schemas
from app.auth import (
    SECRET_KEY,
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    get_current_user,
    Hash,
    authenticate_user,
    create_email_token, oauth2_scheme
)
from app.database import get_db
from app.email import send_verification_email, send_password_reset_email
from app.models import User
from app.schemas import config, UserInDB

# list of allowed origins (domains) for CORS
origins = ["http://localhost:3000"]

app = FastAPI()
hash_handler = Hash()
router = APIRouter(prefix="/users", tags=["users"])
templates = Jinja2Templates(directory="app/templates")

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cloudinary settings for uploading images
cloudinary.config(
    cloud_name=config.CLOUDINARY_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET,
    secure=True,
)


@app.on_event("startup")
async def startup():
    """
    Initializes connection to Redis and sets up request rate limiting with FastAPI Limiter.
    """
    app.redis = await redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=0,
        encoding="utf-8",
        decode_responses=True,
    )
    await FastAPILimiter.init(app.redis)


# Route for getting the home page
@app.get("/")
async def read_root():
    """
    Home page route.

    :return: Welcome message.
    :rtype: dict
    """
    return {"message": "Welcome to the Contact API!"}


@app.post(
    "/register", response_model=schemas.UserInDB, status_code=status.HTTP_201_CREATED
)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Registers a new user in the database and sends a verification email.

    :param user: User registration data.
    :type user: schemas.UserCreate
    :param db: Database session.
    :type db: AsyncSession
    :return: Registered user details.
    :rtype: schemas.UserInDB
    """
    existing_user = await crud.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    hashed_password = await hash_handler.get_password_hash(user.password)
    db_user = await crud.create_user(db, user.email, hashed_password)

    # Send verification email
    await send_verification_email(
        email=user.email,
        username=user.email.split("@")[0],
        host=os.getenv("FRONTEND_URL"),
    )
    return db_user


# Login for getting access token
@app.post("/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    Authenticates a user and returns access and refresh tokens.

    :param form_data: User login data.
    :type form_data: OAuth2PasswordRequestForm
    :param db: Database session.
    :type db: AsyncSession
    :return: Access and refresh tokens.
    :rtype: schemas.Token
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    access_token = await create_access_token(data={"sub": user.email})
    refreshed_token = await create_refresh_token(data={"sub": user.email})
    return schemas.Token(access_token=access_token, refresh_token=refreshed_token)


@app.post("/token/refresh", response_model=schemas.Token)
async def refresh_token(refresh_token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """
    Refreshes the access token using the provided refresh token.

    :param refresh_token: Refresh token for authentication.
    :type refresh_token: str
    :param db: Database session.
    :type db: AsyncSession
    :return: New access token.
    :rtype: dict
    """
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        # Checking if user is active
        user = await crud.get_user_by_email(db, email)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or not active")

        # Creating new access token
        new_access_token = await create_access_token(data={"sub": email})
        return {"access_token": new_access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


@app.post("/request-password-reset/", summary="Request password reset")
async def request_password_reset(email: str, db: AsyncSession = Depends(get_db)):
    """
    Sends a password reset email to the user.

    :param email: User's email address.
    :type email: str
    :param db: Database session.
    :type db: AsyncSession
    :return: Message confirming the password reset link was sent.
    :rtype: dict
    """
    user = await crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Create and send password reset token
    token = await create_email_token({"sub": email})
    await send_password_reset_email(
        email=email, host=os.getenv("FRONTEND_URL"), token=token
    )
    return {"message": "Password reset link sent."}


@app.get("/reset-password-form/{token}", response_class=HTMLResponse)
async def display_reset_password_form(request: Request, token: str):
    """
    Displays the reset password form.

    :param request: HTTP request.
    :type request: Request
    :param token: Password reset token.
    :type token: str
    :return: HTML template for password reset form.
    :rtype: HTMLResponse
    """
    return templates.TemplateResponse("reset_pass_form.html", {"request": request, "token": token})


@app.post("/confirm-password-reset/{token}", summary="Reset password by token")
async def confirm_password_reset(
    token: str, new_password: str = Form(...), db: AsyncSession = Depends(get_db)
):
    """
    Resets the user's password using the provided token.

    :param token: Password reset token.
    :type token: str
    :param new_password: New password to set.
    :type new_password: str
    :param db: Database session.
    :type db: AsyncSession
    :return: Confirmation message.
    :rtype: dict
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload["sub"]
        user = await crud.get_user_by_email(db, email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        hashed_password = await hash_handler.get_password_hash(new_password)
        user.hashed_password = hashed_password
        db.add(user)
        await db.commit()
        return {"message": "Password has been reset."}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )


@app.post(
    "/contacts/",
    response_model=schemas.ContactInDB,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    description="No more than 5 requests per minute allowed",
)
async def create_contact(
    contact: schemas.ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Creates a new contact for the current user.

    :param contact: Contact data.
    :type contact: schemas.ContactCreate
    :param db: Database session.
    :type db: AsyncSession
    :param current_user: Currently authenticated user.
    :type current_user: models.User
    :return: Newly created contact.
    :rtype: schemas.ContactInDB
    """
    return await crud.create_contact(db=db, contact=contact, owner_id=current_user.id)


@app.get("/contacts/", response_model=List[schemas.ContactInDB])
async def read_contacts(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Retrieves all contacts from the database for the current authenticated user.

    :param db: Database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: models.User
    :return: A list of contacts.
    :rtype: List[schemas.ContactInDB]
    """
    return await crud.get_contacts(db=db, owner_id=current_user.id)


@app.get("/contacts/{contact_id}", response_model=schemas.ContactInDB)
async def read_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Retrieves a specific contact from the database by its ID number for the current authenticated user.

    :param contact_id: ID of the contact.
    :type contact_id: int
    :param db: Database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: models.User
    :return: The contact details if found, otherwise raises HTTP 404.
    :rtype: schemas.ContactInDB
    """
    contact = await crud.get_contact(
        db=db, contact_id=contact_id, owner_id=current_user.id
    )
    if contact is None or contact.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found or access denied",
        )
    return contact


@app.put("/contacts/{contact_id}", response_model=schemas.ContactInDB)
async def update_contact(
    contact_id: int,
    contact: schemas.ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Updates a specific contact in the database for the current authenticated user.

    :param contact_id: ID of the contact to update.
    :type contact_id: int
    :param contact: The updated data for the contact.
    :type contact: schemas.ContactUpdate
    :param db: Database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: models.User
    :return: The updated contact if successful, otherwise raises HTTP 404.
    :rtype: schemas.ContactInDB
    """
    existing_contact = await crud.get_contact(
        db=db, contact_id=contact_id, owner_id=current_user.id
    )
    if existing_contact is None or existing_contact.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found or access denied",
        )
    updated_contact = await crud.update_contact(
        db=db, contact_id=contact_id, contact=contact, owner_id=current_user.id
    )
    return updated_contact


@app.delete("/contacts/{contact_id}", response_model=schemas.ContactInDB)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Deletes a specific contact from the database for the current authenticated user.

    :param contact_id: ID of the contact to delete.
    :type contact_id: int
    :param db: Database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: models.User
    :return: The deleted contact if successful, otherwise raises HTTP 404.
    :rtype: schemas.ContactInDB
    """
    contact = await crud.get_contact(db, contact_id, owner_id=current_user.id)
    if contact is None or contact.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found or access denied",
        )
    deleted_contact = await crud.delete_contact(db=db, contact_id=contact_id, owner_id=current_user.id)
    return deleted_contact


@app.get("/contacts/search/", response_model=List[schemas.ContactInDB])
async def search_contacts(
    query: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Searches contacts in the database based on a query for the current authenticated user.

    :param query: Search query for first name, last name, email, or additional info.
    :type query: str
    :param db: Database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: models.User
    :return: A list of contacts matching the search criteria.
    :rtype: List[schemas.ContactInDB]
    """
    return await crud.search_contacts(db=db, query=query, owner_id=current_user.id)


@app.get("/contacts/birthdays/", response_model=List[schemas.ContactInDB])
async def get_upcoming_birthdays(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Retrieves a list of contacts with birthdays in the next 7 days for the current authenticated user from the database.

    :param db: Database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: models.User
    :return: A list of contacts with upcoming birthdays.
    :rtype: List[schemas.ContactInDB]
    """
    return await crud.get_upcoming_birthdays(db=db, owner_id=current_user.id)


@app.get("/auth/confirm_email/{token}")
async def confirm_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Confirms the user's email using a verification token and changes their status to "active" in the database.

    :param token: Email confirmation token.
    :type token: str
    :param db: Database session.
    :type db: AsyncSession
    :return: Confirmation message on success.
    :rtype: dict
    """
    try:
        # decode token to get email
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload["sub"]
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
            )

        # Activate user
        user = await crud.get_user_by_email(db, email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user.is_verified = True
        user.is_active = True
        await db.commit()
        return {"message": "Email confirmed"}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )


@app.patch("/avatar", response_model=UserInDB)
async def update_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Uploads and updates the user's avatar picture using Cloudinary.

    :param file: The uploaded file.
    :type file: UploadFile
    :param current_user: The currently authenticated user.
    :type current_user: User
    :param db: Database session.
    :type db: AsyncSession
    :return: The user object with updated avatar URL.
    :rtype: UserInDB
    """

    result = cloudinary.uploader.upload(
        file.file,
        public_id=f"PD_REST_API_contacts/{current_user.email}",
        overwrite=True,
    )
    avatar_url = result.get("secure_url")

    if not avatar_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar",
        )

    # Update avatar in the database
    updated_user = await crud.update_avatar(
        db=db, email=current_user.email, avatar_url=avatar_url
    )
    return updated_user
