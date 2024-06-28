FROM python:3.11.5

ENV CRYPTOGRAPHY_DONT_BUILD_RUST 1
ENV PYTHONPATH=/code/ PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 POETRY_VIRTUALENVS_CREATE=false

WORKDIR /code

COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt
COPY ./src /code/src
