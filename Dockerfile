FROM python:3.11-alpine

MAINTAINER Thomas Selwyn "thomas@selwyn.tech"

# Update
RUN apk update && apk upgrade && pip install --upgrade pip

# Copy telemetry src into image
WORKDIR /home/cuinspace/ground-station
COPY . .

# Seems to be an issue with this currently
#RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir tornado pyserial

# Run
EXPOSE 33845/udp
CMD ["python", "main.py"]