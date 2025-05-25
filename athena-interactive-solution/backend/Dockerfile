# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed by some Python packages
# (e.g., for Pillow or other libraries that might compile C extensions)
# For this project, it might not be strictly necessary but is good practice.
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application files into the container at /app
# This includes app.py, and the models/ and utils/ directories
COPY . .

# Expose port 5000 to the outside world (the port Gunicorn will run on)
EXPOSE 5000

# Define the command to run the application
# Use Gunicorn as the WSGI server for Flask
# It will look for an 'app' instance in a file named 'app.py'
# workers = 2 --threads = 4 is a common starting point, adjust as needed
# bind to 0.0.0.0 to make it accessible from outside the container
CMD ["gunicorn", "--workers", "2", "--threads", "4", "--bind", "0.0.0.0:5000", "app:app"]
