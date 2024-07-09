# Python-slim base image
FROM python:3.11-slim

MAINTAINER Jacob Terkuc

# Update and upgrade packages
RUN apt-get update && apt-get upgrade -y && pip install --upgrade pip

# Install Virtual Env
RUN pip install virtualenv

# Set the working directory in the container
WORKDIR /app/ground-station

# Copy files
COPY . .

# Set up VENV and "source"
ENV VIRTUAL_ENV=/app/ground-station
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Expose port 33845
EXPOSE 33845/udp

# Run the app when the container launches
CMD ["python3", "main.py"]
