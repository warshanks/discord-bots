# Use Python 3.10-alpine base image
FROM python:3.10-alpine

# Set the working directory inside the container
WORKDIR /app

# Install build dependencies, ffmpeg, and git
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev \
    && apk add --no-cache ffmpeg git

# Copy requirements.txt into the container
COPY ./src/requirements.txt .

# Install dependencies listed in requirements.txt and youtube_dl from GitHub
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir git+https://github.com/ytdl-org/youtube-dl.git@master#egg=youtube_dl

# Remove build dependencies
RUN apk del .build-deps

# Copy the Python scripts, config file, and the supervisord configuration file into the container
COPY ./src .

# Create logs directory inside the container
RUN mkdir /app/logs

# Set supervisord as the entry point, using the provided configuration file
CMD ["supervisord", "-c", "supervisord.conf"]
