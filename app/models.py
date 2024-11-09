from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Date, Boolean, ForeignKey
from app.database import Base
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Contact(Base):
    """
    Represents a contact in the contact list.

    Attributes:
        id (int): The unique identifier of the contact.
        first_name (str): The first name of the contact.
        last_name (str): The last name of the contact.
        email (str): The email address of the contact.
        phone_number (str, optional): The phone number of the contact.
        birthday (Date, optional): The birthdate of the contact.
        additional_info (str, optional): Additional information about the contact.
        owner_id (int): The ID of the user who owns this contact.
        owner (User): The user who owns this contact.
    """
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String, index=True)
    last_name: Mapped[str] = mapped_column(String, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String, nullable=True)
    birthday: Mapped[Date] = mapped_column(Date, nullable=True)
    additional_info: Mapped[str] = mapped_column(String, nullable=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="contacts")


class User(Base):
    """
    Represents a user of the contact list application.

    Attributes:
        id (int): The unique identifier of the user.
        email (str): The email address of the user.
        hashed_password (str): The hashed password of the user.
        is_verified (bool): Whether the user's email is verified.
        is_active (bool): Whether the user is active.
        avatar (str, optional): The URL of the user's avatar.
        contacts (List[Contact]): The list of contacts owned by the user.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    avatar: Mapped[str] = mapped_column(String, nullable=True)
    contacts = relationship("Contact", back_populates="owner")

    def verify_password(self, password: str) -> bool:
        """
        Verifies if the provided password matches the user's hashed password.

        :param password: The plain password to verify.
        :type password: str
        :return: True if the password matches, False otherwise.
        :rtype: bool
        """
        return pwd_context.verify(password, self.hashed_password)

    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        Hashes a plain password using bcrypt.

        :param password: The plain password to hash.
        :type password: str
        :return: The hashed password.
        :rtype: str
        """
        return pwd_context.hash(password)
