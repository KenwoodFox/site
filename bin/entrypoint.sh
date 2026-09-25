#!/bin/sh

./manage.py makemigrations
./manage.py migrate

# Generate initial sitemap
./manage.py ensure_sitemap

# Add cron job to regenerate sitemap every hour
echo "0 */6 * * * /app/manage.py ensure_sitemap >> /var/log/cron.log 2>&1" | crontab -

# Start cron daemon
service cron start

gunicorn kitsunerobotics.wsgi:application \
    --bind 0.0.0.0:80 \
    --workers 2 \
    --worker-class gthread \
    --threads 4 \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5