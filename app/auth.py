import json
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.database import get_db
from starlette import status
from sqlalchemy.future import select
from app import crud


# Setting up tokens and hashing
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

CACHE_EXPIRATION = timedelta(minutes=10)  # cache is stored for 10 minutes


# Class for password hashing
class Hash:
    @staticmethod
    async def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    async def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)


# Function for creating access_token
async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Function for creating refresh_token
async def create_refresh_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


# Function for getting current user by token
async def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token to get user's email
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Caching with Redis
    redis_key = f"user_cache:{email}"
    cached_user = await request.app.redis.get(redis_key)
    if cached_user:
        # Rebuild the User model from cached data
        user_data = json.loads(cached_user)
        user = User(**user_data)
    else:
        # if user is not in cache, retrieve from database
        user = await crud.get_user_by_email(db, email)
        if user is None or not user.is_active or not user.is_verified:
            raise credentials_exception

    # Save user in Redis with expiration time
    await request.app.redis.set(
        redis_key,
        json.dumps({"id": user.id, "email": user.email, "is_verified": user.is_verified, "is_active": user.is_active}),
        ex=CACHE_EXPIRATION)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str):
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
    if user and await Hash.verify_password(password, user.hashed_password):
        return user
    return None


async def create_email_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(hours=1)
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
