#!/bin/bash

PGPASSWORD=postgres psql -h db -U postgres -c "CREATE DATABASE front_docs;"
python3 manage.py migrate
echo "from django.contrib.auth import get_user_model;
User = get_user_model();
User.objects.create_superuser('admin', 'admin@myproject.com', 'admin')" | python3 manage.py shell
python3 manage.py runserver 0.0.0.0:8001

