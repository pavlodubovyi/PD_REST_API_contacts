from typing import List
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, models, schemas
from app.database import engine, get_db

app = FastAPI()


# Route for getting the home page
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Contact API!"}


# Route for creating a new contact
@app.post("/contacts/", response_model=schemas.ContactInDB)
async def create_contact(contact: schemas.ContactCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_contact(db=db, contact=contact)


# Route for getting all contacts
@app.get("/contacts/", response_model=List[schemas.ContactInDB])
async def read_contacts(db: AsyncSession = Depends(get_db)):
    return await crud.get_contacts(db)


# Route for getting a contact by ID
@app.get("/contacts/{contact_id}", response_model=schemas.ContactInDB)
async def read_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    contact = await crud.get_contact(db, contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


# Route for updating a contact
@app.put("/contacts/{contact_id}", response_model=schemas.ContactInDB)
async def update_contact(contact_id: int, contact: schemas.ContactUpdate, db: AsyncSession = Depends(get_db)):
    updated_contact = await crud.update_contact(db, contact_id, contact)
    if updated_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return updated_contact


# Route for deleting a contact
@app.delete("/contacts/{contact_id}", response_model=schemas.ContactInDB)
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    deleted_contact = await crud.delete_contact(db, contact_id)
    if deleted_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return deleted_contact


# Search contacts by first name, last name, email or additional info
@app.get("/contacts/search/", response_model=List[schemas.ContactInDB])
async def search_contacts(query: str, db: AsyncSession = Depends(get_db)):
    return await crud.search_contacts(db, query)


# Get list of contacts with upcoming birthdays for the next 7 days
@app.get("/contacts/birthdays/", response_model=List[schemas.ContactInDB])
async def get_upcoming_birthdays(db: AsyncSession = Depends(get_db)):
    return await crud.get_upcoming_birthdays(db)

