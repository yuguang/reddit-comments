# syntax = docker/dockerfile:1.2

FROM python:2.7

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN mkdir /website
WORKDIR /website
ADD requirements.txt /website/
RUN pip install -r requirements.txt
ADD . /website/

EXPOSE 8000

WORKDIR /website/project

CMD ["gunicorn", "project.wsgi"]