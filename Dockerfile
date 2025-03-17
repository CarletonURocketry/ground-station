# Python-slim base image
FROM python:3.13-slim

LABEL MAINTAINER="Jacob Terkuc"
LABEL MAINTAINER="Elias Hawa"

# Update and upgrade packages
RUN apt-get update && apt-get upgrade -y && pip install --upgrade pip

# Set the working directory in the container
WORKDIR /app/ground-station

# Copy files
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Copy files
COPY . .

# Expose port 33845
EXPOSE 33845/udp

# Run the app when the container launches
CMD ["python", "main.py"]
