from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import Optional
from datetime import date
from pydantic import EmailStr


class ContactBase(BaseModel):
    """
    Base schema for contact data.

    Attributes:
        first_name (str): Contact's first name.
        last_name (str): Contact's last name.
        email (str): Contact's email.
        phone_number (Optional[str], optional): Contact's phone number. Defaults to None.
        birthday (Optional[date], optional): Contact's birthday. Defaults to None.
        additional_info (Optional[str], optional): Additional information about the contact. Defaults to None.
    """
    first_name: str
    last_name: str
    email: str
    phone_number: Optional[str] = None
    birthday: Optional[date] = None
    additional_info: Optional[str] = None


class ContactCreate(ContactBase):
    """
    Schema for creating a new contact.
    Inherits all attributes from ContactBase.
    """
    pass


class ContactUpdate(ContactBase):
    """
    Schema for updating an existing contact.
    Inherits all attributes from ContactBase.
    """
    pass


class ContactInDB(ContactBase):
    """
    Schema for a contact stored in the database.

    Attributes:
        id (int): The unique identifier of the contact.
    """
    id: int

    class Config:
        """
        Configuration for Pydantic model behavior.

        Attributes:
            from_attributes (bool): Allows the model to populate fields directly
            from ORM model attributes, facilitating the use of ORM objects with
            Pydantic models.
        """
        from_attributes = True


class UserBase(BaseModel):
    """
    Base schema for user data.

    Attributes:
        email (EmailStr): User's email address.
    """
    email: EmailStr


class UserCreate(UserBase):
    """
    Schema for creating a new user.

    Attributes:
        password (str): User's password.
    """
    password: str


class UserInDB(UserBase):
    """
    Schema for a user stored in the database.

    Attributes:
        id (int): The unique identifier of the user.
        is_verified (bool): Whether the user's email is verified.
        is_active (bool): Whether the user is active.
        avatar (Optional[str], optional): The URL of the user's avatar. Defaults to None.
    """
    id: int
    is_verified: bool
    is_active: bool
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """
    Schema for token data.

    Attributes:
        access_token (str): The access token for user authentication.
        refresh_token (str): The refresh token for obtaining new access tokens.
        token_type (str): The type of token, default is "bearer".
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AppConfig(BaseSettings):
    """
    Configuration settings for the application, loaded from environment variables.

    Attributes:
        POSTGRES_DB (str): The PostgreSQL database name.
        POSTGRES_USER (str): The PostgreSQL username.
        POSTGRES_PASSWORD (str): The PostgreSQL user password.
        SYNC_DATABASE_URL (str): The synchronous database URL.
        REDIS_HOST (str): The Redis host.
        REDIS_PORT (int): The Redis port.
        DATABASE_URL (str): The asynchronous database URL.
        SECRET_KEY (str): The secret key for JWT encoding.
        EMAIL_USER (str): The email account username.
        EMAIL_PASS (str): The email account password.
        EMAIL_FROM (str): The sender's email address.
        SMTP_SERVER (str): The SMTP server for email.
        EMAIL_PORT (int): The port for the SMTP server.
        FRONTEND_URL (str): The frontend URL for email links.
        CLOUDINARY_NAME (str): The Cloudinary account name.
        CLOUDINARY_API_KEY (str): The Cloudinary API key.
        CLOUDINARY_API_SECRET (str): The Cloudinary API secret.
        CLOUDINARY_URL (str): The Cloudinary URL for image uploads.
    """
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    SYNC_DATABASE_URL: str
    REDIS_HOST: str
    REDIS_PORT: int
    DATABASE_URL: str
    SECRET_KEY: str
    EMAIL_USER: str
    EMAIL_PASS: str
    EMAIL_FROM: str
    SMTP_SERVER: str
    EMAIL_PORT: int
    FRONTEND_URL: str
    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    CLOUDINARY_URL: str

    class Config:
        """
        Configuration settings for environment variable handling.

        Attributes:
            env_file (str): Specifies the file from which environment variables should be loaded.
            env_file_encoding (str): The encoding format for the environment file.
        """
        env_file = ".env"
        env_file_encoding = "utf-8"


config = AppConfig()
