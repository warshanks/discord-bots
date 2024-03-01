FROM python:3.13.0a4-slim

WORKDIR /app

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y --no-install-recommends ffmpeg git
RUN rm -rf /var/lib/apt/lists/*

COPY ./src/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir git+https://github.com/ytdl-org/youtube-dl.git@master#egg=youtube-dl

COPY ./src .

CMD ["supervisord", "-c", "/app/supervisord.conf"]
