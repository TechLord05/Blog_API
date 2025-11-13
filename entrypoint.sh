#!/bin/sh

# Exit on errors
set -e

# Run database migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files (optional)
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the app with Gunicorn (production)
echo "Starting server..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --log-level info
