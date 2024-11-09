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

# Set up password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

CACHE_EXPIRATION = timedelta(minutes=10)  # cache is stored for 10 minutes


class Hash:
    """
    Utility class for password hashing and verification.
    """

    @staticmethod
    async def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify the plain password against the hashed password.

        :param plain_password: The plaintext password to verify.
        :type plain_password: str
        :param hashed_password: The hashed password to verify against.
        :type hashed_password: str
        :return: True if the passwords match, otherwise False.
        :rtype: bool
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    async def get_password_hash(password: str) -> str:
        """
        Hash the provided password.

        :param password: The plaintext password to hash.
        :type password: str
        :return: The hashed password.
        :rtype: str
        """
        return pwd_context.hash(password)


async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new access token with an expiration time.

    :param data: The payload data to include in the token.
    :type data: dict
    :param expires_delta: Optional expiration delta for the token.
    :type expires_delta: Optional[timedelta]
    :return: The encoded JWT access token.
    :rtype: str
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def create_refresh_token(data: dict) -> str:
    """
    Create a new refresh token with a fixed expiration time.

    :param data: The payload data to include in the token.
    :type data: dict
    :return: The encoded JWT refresh token.
    :rtype: str
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Retrieve the current user based on the provided JWT token.

    :param request: The HTTP request object, used for Redis cache access.
    :type request: Request
    :param token: The JWT token extracted from the request.
    :type token: str
    :param db: The database session.
    :type db: AsyncSession
    :return: The user associated with the token.
    :rtype: User
    :raises HTTPException: If the token is invalid or user cannot be authenticated.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Attempt to retrieve user from Redis cache
    redis_key = f"user_cache:{email}"
    cached_user = await request.app.redis.get(redis_key)
    if cached_user:
        user_data = json.loads(cached_user)
        user = User(**user_data)
    else:
        # Retrieve user from the database if not in cache
        user = await crud.get_user_by_email(db, email)
        if user is None or not user.is_active or not user.is_verified:
            raise credentials_exception

        # Cache the user data in Redis
        await request.app.redis.set(
            redis_key,
            json.dumps(
                {
                    "id": user.id,
                    "email": user.email,
                    "is_verified": user.is_verified,
                    "is_active": user.is_active,
                }
            ),
            ex=CACHE_EXPIRATION,
        )

    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by verifying their email and password.

    :param db: The database session.
    :type db: AsyncSession
    :param email: The user's email address.
    :type email: str
    :param password: The user's plaintext password.
    :type password: str
    :return: The authenticated user object if authentication is successful, else None.
    :rtype: Optional[User]
    """
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
    if user and await Hash.verify_password(password, user.hashed_password):
        return user
    return None


async def create_email_token(data: dict) -> str:
    """
    Create a short-living email token, typically used for email verification or password reset.

    :param data: The payload data to include in the token.
    :type data: dict
    :return: The encoded JWT email token.
    :rtype: str
    """
    expire = datetime.utcnow() + timedelta(hours=1)
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
