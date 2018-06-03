#Grab the latest alpine image
FROM alpine:latest

# Install missing Alpine dependencies
RUN apk add --no-cache gcc musl-dev linux-headers

# Install python3 and pip
RUN apk add --no-cache --update python3 python3-dev py3-pip bash

# Install dependencies
ADD ./app/requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Add our code
ADD ./app /opt/app/
WORKDIR /opt/app

# Run the image as a non-root user
RUN adduser -D myuser
USER myuser

# Expose is NOT supported by Heroku
# EXPOSE 5000

# Run the app.  CMD is required to run on Heroku
# $PORT is set by Heroku            
CMD gunicorn --bind 0.0.0.0:$PORT wsgi 
