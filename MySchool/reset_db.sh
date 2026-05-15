#!/bin/bash
cd /home/gioaziz/Projects/MySchool3.5/MySchool

echo "Pulizia DB e Migrations vecchie..."
rm -f db.sqlite3
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc"  -delete
rm -rf users/migrations/__pycache__ core/migrations/__pycache__ tenants/migrations/__pycache__

echo "Creazione Migrations..."
python manage.py makemigrations users
python manage.py makemigrations core tenants
python manage.py makemigrations

echo "Esecuzione Migrate..."
python manage.py migrate

echo "Seed Dati..."
python manage.py seed_db

echo "Fatto! Ora puoi avviare il server: python manage.py runserver"
