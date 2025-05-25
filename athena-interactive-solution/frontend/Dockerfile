# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (if any are ever needed, though less common for pure Streamlit/requests)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the frontend application files into the container at /app
# This is primarily app.py for Streamlit
COPY . .

# Expose port 8501 to the outside world (the default Streamlit port)
EXPOSE 8501

# Define the command to run the Streamlit application
# Tells Streamlit to run app.py and listen on all network interfaces
# --server.address=0.0.0.0 allows it to be accessible from outside the container
# --server.port=8501 specifies the port
# --server.headless=true is recommended for running in Docker/non-interactive environments
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
