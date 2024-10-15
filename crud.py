from sqlalchemy.orm import Session
from sqlalchemy import or_
import models
import schemas
from datetime import datetime, timedelta


# Create new contact
def create_contact(db: Session, contact: schemas.ContactCreate):
    db_contact = models.Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


# Get all contacts
def get_contacts(db: Session):
    return db.query(models.Contact).all()


# Get contact by id
def get_contact(db: Session, contact_id: int):
    return db.query(models.Contact).filter(models.Contact.id == contact_id).first()


# Update contact
def update_contact(db: Session, contact_id: int, contact: schemas.ContactUpdate):
    db_contact = get_contact(db, contact_id)
    if db_contact:
        for key, value in contact.dict(exclude_unset=True).items():
            setattr(db_contact, key, value)
        db.commit()
        db.refresh(db_contact)
    return db_contact


# Delete contact
def delete_contact(db: Session, contact_id: int):
    db_contact = get_contact(db, contact_id)
    if db_contact:
        db.delete(db_contact)
        db.commit()
    return db_contact


# Search contacts by first name, last name or email
def search_contacts(db: Session, query: str):
    return db.query(models.Contact).filter(
        or_(
            models.Contact.first_name.ilike(f"%{query}%"),
            models.Contact.last_name.ilike(f"%{query}%"),
            models.Contact.email.ilike(f"%{query}%"),
            models.Contact.additional_info.ilike(f"%{query}%")
        )
    ).all()


# Get list of contacts with upcoming birthdays for the next 7 days
def get_upcoming_birthdays(db: Session):
    today = datetime.today().date()
    upcoming = today + timedelta(days=7)
    contacts = db.query(models.Contact).all()

    upcoming_birthdays = []
    for contact in contacts:
        if contact.birthday:
            birthday_this_year = contact.birthday.replace(year=today.year)
            if today <= birthday_this_year <= upcoming:
                upcoming_birthdays.append(contact)

    return upcoming_birthdays
