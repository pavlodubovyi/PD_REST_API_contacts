API Modules Documentation
=========================

This document provides in-depth documentation for the core API modules in the Contact List REST API project.

.. toctree::
   :maxdepth: 2

Main Application Module
-----------------------
.. automodule:: app.main
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

This module (`app.main`) serves as the main entry point for the application. It contains the FastAPI application instance and key configurations.

Authentication Module
---------------------
.. automodule:: app.auth
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

The authentication module (`app.auth`) provides user authentication logic. It includes functions for JWT token handling, password hashing, and email verification.

CRUD Operations Module
----------------------
.. automodule:: app.crud
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

The CRUD module (`app.crud`) handles database operations for creating, reading, updating, and deleting records in the contact and user tables. It abstracts the database layer, making the logic reusable and clean.

Database Configuration
----------------------
.. automodule:: app.database
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

This module (`app.database`) includes the database setup and configuration, as well as functions for connecting to the PostgreSQL database. It initializes the database engine and session makers.

Email Module
------------
.. automodule:: app.email
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

The email module (`app.email`) handles sending emails to users. It includes functions for sending verification emails and password reset emails.