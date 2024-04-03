FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY . .
COPY requirements.txt /temp/requirements.txt

WORKDIR /bot
EXPOSE 8000


RUN pip install --upgrade pip
RUN pip install -r /temp/requirements.txt