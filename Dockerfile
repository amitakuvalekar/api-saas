# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Set environment variables for database connection (replace with your actual credentials or use a secret management system in production)
ENV DB_HOST="sql.freedb.tech"
ENV DB_USER="freedb_amysocial"
ENV DB_PASSWORD="nQ2p!a&EFq%EgsK"
ENV DB_NAME="freedb_winedb"
ENV DB_PORT="3306"

# Install any needed packages specified in requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add a non-root user and switch to it
RUN adduser --system --no-create-home appuser
USER appuser

# Copy the current directory contents into the container at /app
COPY ./src /app/src
COPY wine.csv /app/

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the uvicorn server
# The --host 0.0.0.0 makes the server accessible from outside the container
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
