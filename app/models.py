from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Date
from app.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String, index=True)
    last_name: Mapped[str] = mapped_column(String, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String, nullable=True)
    birthday: Mapped[Date] = mapped_column(Date, nullable=True)
    additional_info: Mapped[str] = mapped_column(String, nullable=True)
