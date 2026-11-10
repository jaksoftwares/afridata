#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🔄 Waiting for database..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done
echo "✅ Database is ready!"

echo "🛠 Checking for legacy migrations..."
python sync_legacy_db.py

echo "🛠 Running migrations..."
python manage.py migrate

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

if [ "$DJANGO_SUPERUSER_USERNAME" ]
then
  echo "👤 Creating env-based superuser..."
  python manage.py createsuperuser \
    --noinput \
    --username "$DJANGO_SUPERUSER_USERNAME" \
    --email "$DJANGO_SUPERUSER_EMAIL"
fi

echo "👤 Setting up predefined super admins..."
python setup_admins.py

echo "🚀 Starting Gunicorn server..."
# --timeout: the default 30s kills uploads that are still arriving or being hashed
# (a 2GB file on a slow link takes minutes). 900s covers the largest allowed upload.
# --worker-class gthread --threads: a long upload holds one thread, not the whole worker,
# so the rest of the site stays responsive while large files arrive.
exec gunicorn afridata.wsgi:application --bind 0.0.0.0:8000 --limit-request-field_size 32768 --timeout 900 --worker-class gthread --workers 3 --threads 8
