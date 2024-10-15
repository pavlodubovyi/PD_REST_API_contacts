from typing import List

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

import crud
import models
import schemas
from database import engine, get_db

# Database initialization
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Route for creating a new contact
@app.post("/contacts/", response_model=schemas.ContactInDB)
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    return crud.create_contact(db=db, contact=contact)


# Route for getting the home page
@app.get("/")
def read_root():
    return {"message": "Welcome to the Contact API!"}


# Route for getting all contacts
@app.get("/contacts/", response_model=List[schemas.ContactInDB])
def read_contacts(db: Session = Depends(get_db)):
    return crud.get_contacts(db)


# Route for getting a contact by ID
@app.get("/contacts/{contact_id}", response_model=schemas.ContactInDB)
def read_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = crud.get_contact(db, contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


# Route for updating a contact
@app.put("/contacts/{contact_id}", response_model=schemas.ContactInDB)
def update_contact(contact_id: int, contact: schemas.ContactUpdate, db: Session = Depends(get_db)):
    updated_contact = crud.update_contact(db, contact_id, contact)
    if updated_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return updated_contact


# Route for deleting a contact
@app.delete("/contacts/{contact_id}", response_model=schemas.ContactInDB)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    deleted_contact = crud.delete_contact(db, contact_id)
    if deleted_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return deleted_contact


# Search contacts by first name, last name, email or additional info
@app.get("/contacts/search/", response_model=List[schemas.ContactInDB])
def search_contacts(query: str, db: Session = Depends(get_db)):
    return crud.search_contacts(db, query)


# Get list of contacts with upcoming birthdays for the next 7 days
@app.get("/contacts/birthdays/", response_model=List[schemas.ContactInDB])
def get_upcoming_birthdays(db: Session = Depends(get_db)):
    return crud.get_upcoming_birthdays(db)

