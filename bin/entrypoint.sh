#!/bin/sh

./manage.py migrate

# Pull markdown posts
./manage.py load_blog || echo "Blog load failed"

# Generate initial sitemap
./manage.py ensure_sitemap

# Supercronic
supercronic -test /app/bin/crontab || exit 1
supercronic /app/bin/crontab &

gunicorn kitsunerobotics.wsgi:application \
    --bind 0.0.0.0:80 \
    --workers 2 \
    --worker-class gthread \
    --threads 4 \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5