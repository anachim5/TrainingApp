# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install pipenv and importlib_metadata
RUN pip install pipenv importlib_metadata

# Copy the Pipfile and Pipfile.lock to the working directory
COPY Pipfile Pipfile.lock ./

# Install the dependencies
RUN pipenv install --system --deploy --ignore-pipfile

# Copy the rest of the application code
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 7777

# Run the application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7777"]
