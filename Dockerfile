# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install poetry
RUN pip install poetry

# Copy only the poetry-related files (pyproject.toml and poetry.lock)
COPY pyproject.toml poetry.lock /app/

# Set the working directory in the container
WORKDIR /app

# Install project dependencies
RUN poetry install --no-root --no-interaction --no-ansi

# Copy the rest of the application code
COPY . /app

# Expose the port number the FastAPI app runs on
EXPOSE 8000

# Run the FastAPI app using uvicorn
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]
