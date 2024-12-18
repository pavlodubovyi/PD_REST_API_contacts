# Contact List API

This project is a REST API for managing a contact list. It is built using FastAPI and SQLAlchemy, and uses PostgreSQL as the database, and Pydantic for data validation. The API supports full CRUD operations (Create, Read, Update, Delete) for contacts, as well as user authentication, search functionality and birthday reminders for the upcoming 7 days.

## Features

- User Registration and Authentication: Register new users and authenticate with JWT tokens. Registerd users can
- Create new contacts with personal details (name, email, phone, birthday, additional info)
- Retrieve a list of all contacts
- Search contacts by first name, last name, email, phone number, or additional info
- Update contact information
- Delete contact
- Get a list of contacts with birthdays in the next 7 days

## Installation

### Prerequisites
Ensure the following are installed:
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Steps
1. Clone the repository
   ```bash
   git clone https://github.com/your-username/pd-rest-api-contacts.git
   cd pd-rest-api-contacts

2. Set up environment variables
Copy the example environment file (.env.example) to .env, and configure the required variables in .env:
   ```bash
   cp .env.example .env

Set values for the following variables:

- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` - PostgreSQL configuration
- `DATABASE_URL` - Connection URL for PostgreSQL
- `REDIS_HOST` and `REDIS_PORT` - Redis configuration
- `SECRET_KEY` - JWT token generation
- `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_FROM`, `SMTP_SERVER`, `EMAIL_PORT` - Email configuration
- `CLOUDINARY_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_URL` - Cloudinary avatar upload

3. Build and start the Docker containers

Use `Docker Compose` to build and run the PostgreSQL, Redis, and FastAPI application containers:
   ```bash
  docker-compose up --build
   ```

This command will:
- Build the application image using the ``Dockerfile``.
- Set up a ``PostgreSQL`` container as the database.
- Set up a ``Redis`` container for caching.
- Start the ``FastAPI`` application on http://127.0.0.1:8001.
- Make ``Sphinx`` documentation available on http://127.0.0.2

4. Verify the containers

After starting, ensure the following services are running:
- ``FastAPI`` application: Access the API at http://127.0.0.1:8001.
- ``PostgreSQL`` database and ``Redis``: Available within the Docker network.

To view logs and confirm service startup:
   ```bash
docker-compose logs -f
   ```

5. Access the API documentation

Interactive API documentation is available at:

- Swagger UI: http://127.0.0.1:8001/docs
- ReDoc: http://127.0.0.1:8001/redoc

### Running Commands Directly (Optional)
For development or testing, you can run commands directly within the ``Docker`` container.

Access the running ``web`` container:
```bash
docker-compose exec web /bin/bash
```
Run commands (e.g., migrations or testing):
```
poetry run alembic upgrade head  # Run migrations
poetry run pytest                 # Run tests
```
This setup fully containerizes all dependencies, including ``PostgreSQL``, ``Redis``, and ``FastAPI``, ensuring easy deployment and testing.

## Usage

- `POST` /register - Register a new user
- `POST` /login - Login to receive access and refresh tokens
- `POST` /contacts/ - Create a new contact (rate limited)
- `GET` /contacts/ - Retrieve all contacts
- `GET` /contacts/{contact_id} - Retrieve a contact by ID
- `PUT` /contacts/{contact_id} - Update a contact by ID
- `DELETE` /contacts/{contact_id} - Delete a contact by ID
- `GET` /contacts/search/ - Search contacts by query
- `GET` /contacts/birthdays/ - Retrieve contacts with birthdays in the next 7 days
- `POST` /request-password-reset/ - Request a password reset link
- `POST` /confirm-password-reset/{token} - Reset password with the token
- `PATCH` /avatar - Upload or update avatar
## Project Structure
```
.
├── .env                # Environment variables
├── main.py             # FastAPI application
├── models.py           # SQLAlchemy models
├── schemas.py          # Pydantic schemas
├── crud.py             # CRUD operations
├── database.py         # Database configuration and connection
├── pyproject.toml      # Poetry configuration file
├── README.md           # Project documentation
└── requirements.txt    # Auto-generated by Poetry (optional)
```
