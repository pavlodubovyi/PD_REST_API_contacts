from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select
from app import models, schemas
from datetime import datetime, timedelta


# Create new contact
async def create_contact(db: AsyncSession, contact: schemas.ContactCreate):
    db_contact = models.Contact(**contact.dict())
    db.add(db_contact)
    await db.commit()
    await db.refresh(db_contact)
    return db_contact


# Get all contacts
async def get_contacts(db: AsyncSession):
    result = await db.execute(select(models.Contact))
    return result.scalars().all()


# Get contact by id
async def get_contact(db: AsyncSession, contact_id: int):
    result = await db.execute(select(models.Contact).filter(models.Contact.id == contact_id))
    return result.scalar_one_or_none()


# Update contact
async def update_contact(db: AsyncSession, contact_id: int, contact: schemas.ContactUpdate):
    db_contact = await get_contact(db, contact_id)
    if db_contact:
        for key, value in contact.dict(exclude_unset=True).items():
            setattr(db_contact, key, value)
        await db.commit()
        await db.refresh(db_contact)
    return db_contact


# Delete contact
async def delete_contact(db: AsyncSession, contact_id: int):
    db_contact = await get_contact(db, contact_id)
    if db_contact:
        await db.delete(db_contact)
        await db.commit()
    return db_contact


# Search contacts by first name, last name or email
async def search_contacts(db: AsyncSession, query: str):
    result = await db.execute(
        select(models.Contact).filter(
            or_(
                models.Contact.first_name.ilike(f"%{query}%"),
                models.Contact.last_name.ilike(f"%{query}%"),
                models.Contact.email.ilike(f"%{query}%"),
                models.Contact.additional_info.ilike(f"%{query}%")
            )
        )
    )
    return result.scalars().all()


# Get list of contacts with upcoming birthdays for the next 7 days
async def get_upcoming_birthdays(db: AsyncSession):
    today = datetime.today().date()
    upcoming = today + timedelta(days=7)
    result = await db.execute(select(models.Contact))
    contacts = result.scalars().all()

    upcoming_birthdays = []
    for contact in contacts:
        if contact.birthday:
            birthday_this_year = contact.birthday.replace(year=today.year)
            if today <= birthday_this_year <= upcoming:
                upcoming_birthdays.append(contact)

    return upcoming_birthdays
