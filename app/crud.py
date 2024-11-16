from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select
from app import models, schemas
from datetime import datetime, timedelta


async def create_contact(
    db: AsyncSession, contact: schemas.ContactCreate, owner_id: int
):
    """
    Creates a new contact for a specific user.

    :param db: The database session.
    :type db: AsyncSession
    :param contact: The data for the new contact.
    :type contact: schemas.ContactCreate
    :param owner_id: The ID of the user who owns the contact.
    :type owner_id: int
    :return: The newly created contact.
    :rtype: models.Contact
    """
    db_contact = models.Contact(**contact.model_dump(), owner_id=owner_id)
    db.add(db_contact)
    await db.commit()
    await db.refresh(db_contact)
    return db_contact


async def get_contacts(db: AsyncSession, owner_id: int):
    """
    Retrieves all contacts of a specific user from database.

    :param db: The database session.
    :type db: AsyncSession
    :param owner_id: The ID of the user who owns the contacts.
    :type owner_id: int
    :return: A list of contacts belonging to the user.
    :rtype: list[models.Contact]
    """
    result = await db.execute(
        select(models.Contact).filter(models.Contact.owner_id == owner_id)
    )
    return result.scalars().all()


async def get_contact(db: AsyncSession, contact_id: int, owner_id: int):
    """
    Retrieves a specific contact by its ID, ensuring it belongs to the user.

    :param db: The database session.
    :type db: AsyncSession
    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param owner_id: The ID of the user who owns the contact.
    :type owner_id: int
    :return: The contact if found, otherwise None.
    :rtype: models.Contact | None
    """
    result = await db.execute(
        select(models.Contact).filter(
            models.Contact.id == contact_id, models.Contact.owner_id == owner_id
        )
    )
    return result.scalar_one_or_none()


async def update_contact(
    db: AsyncSession, contact_id: int, contact: schemas.ContactUpdate, owner_id: int
):
    """
    Updates a specific contact's information, ensuring it belongs to the user.

    :param db: The database session.
    :type db: AsyncSession
    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param contact: The updated data for the contact.
    :type contact: schemas.ContactUpdate
    :param owner_id: The ID of the user who owns the contact.
    :type owner_id: int
    :return: The updated contact if found, otherwise None.
    :rtype: models.Contact | None
    """
    db_contact = await get_contact(db, contact_id, owner_id)
    if db_contact:
        for key, value in contact.model_dump(exclude_unset=True).items():
            setattr(db_contact, key, value)
        await db.commit()
        await db.refresh(db_contact)
    return db_contact


async def delete_contact(db: AsyncSession, contact_id: int, owner_id: int):
    """
    Deletes a specific contact, ensuring it belongs to the user.

    :param db: The database session.
    :type db: AsyncSession
    :param contact_id: The ID of the contact to delete.
    :type contact_id: int
    :param owner_id: The ID of the user who owns the contact.
    :type owner_id: int
    :return: The deleted contact if found, otherwise None.
    :rtype: models.Contact | None
    """
    db_contact = await get_contact(db, contact_id, owner_id)
    if db_contact:
        await db.delete(db_contact)
        await db.commit()
    return db_contact


async def search_contacts(db: AsyncSession, query: str, owner_id: int):
    """
    Searches database for one or more contacts by first name, last name, email, or additional info.

    :param db: The database session.
    :type db: AsyncSession
    :param query: The search query string.
    :type query: str
    :param owner_id: The ID of the user who owns the contacts.
    :type owner_id: int
    :return: A list of contacts matching the search criteria.
    :rtype: list[models.Contact]
    """
    result = await db.execute(
        select(models.Contact).filter(
            or_(
                models.Contact.first_name.ilike(f"%{query}%"),
                models.Contact.last_name.ilike(f"%{query}%"),
                models.Contact.email.ilike(f"%{query}%"),
                models.Contact.additional_info.ilike(f"%{query}%"),
            ),
            models.Contact.owner_id == owner_id,
        )
    )
    return result.scalars().all()


async def get_upcoming_birthdays(db: AsyncSession, owner_id: int):
    """
    Retrieves a list of contacts with birthdays in the next 7 days for a specific user.

    :param db: The database session.
    :type db: AsyncSession
    :param owner_id: The ID of the user who owns the contacts.
    :type owner_id: int
    :return: A list of contacts with upcoming birthdays.
    :rtype: list[models.Contact]
    """
    today = datetime.today().date()
    upcoming = today + timedelta(days=7)
    result = await db.execute(
        select(models.Contact).filter(models.Contact.owner_id == owner_id)
    )
    contacts = result.scalars().all()

    upcoming_birthdays = []
    for contact in contacts:
        if contact.birthday:
            birthday_this_year = contact.birthday.replace(year=today.year)
            if today <= birthday_this_year <= upcoming:
                upcoming_birthdays.append(contact)

    return upcoming_birthdays


# User operations
async def get_user_by_email(db: AsyncSession, email: str):
    """
    Retrieves a user from database by his/her email address.

    :param db: The database session.
    :type db: AsyncSession
    :param email: The user's email address.
    :type email: str
    :return: The user if found, otherwise None.
    :rtype: models.User | None
    """
    result = await db.execute(select(models.User).filter(models.User.email == email))
    return result.scalar_one_or_none()


# Create new user
async def create_user(db: AsyncSession, email: str, hashed_password: str):
    """
    Creates a new user with the specified email and hashed password.

    :param db: The database session.
    :type db: AsyncSession
    :param email: The user's email address.
    :type email: str
    :param hashed_password: The hashed password for the user.
    :type hashed_password: str
    :return: The newly created user.
    :rtype: models.User
    """
    db_user = models.User(email=email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


# Update avatar
async def update_avatar(db: AsyncSession, email: str, avatar_url: str) -> models.User:
    """
    Updates the user's avatar URL.

    :param db: The database session.
    :type db: AsyncSession
    :param email: The user's email address.
    :type email: str
    :param avatar_url: The new avatar URL for the user.
    :type avatar_url: str
    :return: The updated user with the new avatar URL.
    :rtype: models.User
    """
    user = await get_user_by_email(db, email)
    if user:
        user.avatar = avatar_url
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user
