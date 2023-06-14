FROM python:slim

WORKDIR /app

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

COPY ./src/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir git+https://github.com/ytdl-org/youtube-dl.git@master#egg=youtube-dl

COPY ./src .

CMD ["supervisord", "-c", "/app/supervisord.conf"]
