# Start with a lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install GCC and other necessary build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy the Poetry files first for dependency resolution
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root

# Copy the rest of the application code
COPY . .

# Expose the port that FastAPI will run on
EXPOSE 8001

# Command to run the FastAPI server
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
