FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends ffmpeg git libportaudio2 python3-pyaudio && \
    rm -rf /var/lib/apt/lists/*

# create the directory in the container
RUN mkdir -p /app/ff1_cache/Data

COPY ./src/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir git+https://github.com/ytdl-org/youtube-dl.git@master#egg=youtube-dl

COPY ./src .

RUN mkdir /app/logs

CMD ["supervisord", "-c", "/app/supervisord.conf"]
