FROM python:3.12-slim-bookworm AS production

RUN apt-get update && apt-get install -y curl

WORKDIR /backend

RUN python -m pip install --upgrade pip

COPY requirements.txt /backend/
RUN pip install --no-cache-dir \ 
    -r requirements.txt

COPY . .
