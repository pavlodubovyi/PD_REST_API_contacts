Installation
============

Prerequisites
-------------

Ensure the following are installed:

- **Docker**: `https://docs.docker.com/get-docker/`
- **Docker Compose**: `https://docs.docker.com/compose/install/`

Steps
-----

1. **Clone the repository**

   .. code-block:: bash

      git clone https://github.com/your-username/pd-rest-api-contacts.git
      cd pd-rest-api-contacts

2. **Set up environment variables**

   Copy the example environment file (`.env.example`) to `.env`, and configure the required variables in `.env`:

   .. code-block:: bash

      cp .env.example .env

   Set values for the following variables:

   - ``POSTGRES_DB``, ``POSTGRES_USER``, ``POSTGRES_PASSWORD`` - PostgreSQL configuration
   - ``DATABASE_URL`` - Connection URL for PostgreSQL
   - ``REDIS_HOST`` and ``REDIS_PORT`` - Redis configuration
   - ``SECRET_KEY`` - JWT token generation
   - ``EMAIL_USER``, ``EMAIL_PASS``, ``EMAIL_FROM``, ``SMTP_SERVER``, ``EMAIL_PORT`` - Email configuration
   - ``CLOUDINARY_NAME``, ``CLOUDINARY_API_KEY``, ``CLOUDINARY_API_SECRET``, ``CLOUDINARY_URL`` - Cloudinary avatar upload

3. **Build and start the Docker containers**

   Use Docker Compose to build and run the PostgreSQL, Redis, and FastAPI application containers:

   .. code-block:: bash

      docker-compose up --build

   This command will:

   - Build the application image using the ``Dockerfile``.
   - Set up a PostgreSQL container as the database.
   - Set up a Redis container for caching.
   - Start the FastAPI application on ``http://127.0.0.1:8001``.

   .. note::

      Redis will start automatically as part of the Docker Compose setup defined in ``docker-compose.yml``.

4. **Verify the containers**

   After starting, ensure the following services are running:

   - **FastAPI application**: Access the API at ``http://127.0.0.1:8001``.
   - **PostgreSQL database** and **Redis**: Available within the Docker network.

   To view logs and confirm service startup:

   .. code-block:: bash

      docker-compose logs -f

5. **Access the API documentation**

   Interactive API documentation is available at:

   - **Swagger UI**: ``http://127.0.0.1:8001/docs``
   - **ReDoc**: ``http://127.0.0.1:8001/redoc``

Running Commands Directly (Optional)
------------------------------------

For development or testing, you can run commands directly within the Docker container.

1. **Access the running ``web`` container**:

   .. code-block:: bash

      docker-compose exec web /bin/bash

2. **Run commands** (e.g., migrations or testing):

   .. code-block:: bash

      poetry run alembic upgrade head  # Run migrations
      poetry run pytest                 # Run tests

This setup fully containerizes all dependencies, including PostgreSQL, Redis, and FastAPI, ensuring easy deployment and testing.
