FROM python:3.12

RUN mkdir /django_frontend

WORKDIR /django_frontend

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*``

COPY . .

RUN chmod a+x /django_frontend/for_docker/*.sh

WORKDIR /django_frontend/sitepytesseract

EXPOSE 8001

