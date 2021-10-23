# syntax = docker/dockerfile:1.2

FROM python:2.7

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV RENDER true

RUN mkdir /sqlite
ADD ./sqlite/db.sqlite3 /sqlite/db.sqlite3

# install dependencies
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN mkdir /website
WORKDIR /website
ADD requirements.txt /website/
RUN pip install -r requirements.txt
ADD . /website/

EXPOSE 8000

WORKDIR /website/project
RUN python manage.py collectstatic --no-input
#RUN python manage.py migrate

CMD ["gunicorn", "project.wsgi", "--bind", "0.0.0.0:8000"]