from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import Optional
from datetime import date
from pydantic import EmailStr


class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: Optional[str] = None
    birthday: Optional[date] = None
    additional_info: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(ContactBase):
    pass


class ContactInDB(ContactBase):
    id: int

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    id: int
    is_verified: bool
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AppConfig(BaseSettings):
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
        env_file = ".env"


config = AppConfig()
