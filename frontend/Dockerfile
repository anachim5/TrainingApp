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

# Make port 5010 available to the world outside this container
EXPOSE 5010

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Run the application
CMD ["flask", "run"]