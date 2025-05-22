#!/bin/bash
# Exit on error
set -o errexit

# Install dependencies
python -m pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py makemigrations

# Apply database migrations
python manage.py migrate

echo "Build process completed."

export DJANGO_SETTINGS_MODULE=InventoryManagement.settings
