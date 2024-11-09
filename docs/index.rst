.. Contact List REST API on FastAPI documentation master file, created by
   sphinx-quickstart on Fri Nov  8 13:41:45 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Contact List REST API on FastAPI documentation
==============================================

Introduction
============

The Contact List API is a REST API for managing a contact list. It supports CRUD operations (Create, Read, Update, Delete) for contacts, user authentication with JWT tokens, password reset functionality, search capabilities, and upcoming birthday reminders.

Features
========

Below is an overview of the main features available in the Contact List API.

**User Registration and Authentication**
- Register a new user and log in to receive a JWT token for secure access.

**Password Reset**
- Request a password reset link and reset your password securely via email.

**Contact Management** (only for authenticated users)
- Create, read, update, and delete contacts with fields like name, email, phone number, birthday, and additional info.

**Search and Filter** (only for authenticated users)
- Search contacts by name, email, or other details, and get a list of upcoming birthdays for the next 7 days.

**Rate Limiting**
- Limits the number of requests to the contact creation endpoint to prevent abuse.

**Avatar Management**
- Upload or update a user's avatar via Cloudinary.

Contents
========

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   functionality
   models
   schemas
   api_models_documentation
   utilities
   templates
