#!/bin/sh

./manage.py migrate

# Pull markdown posts
./manage.py load_blog || echo "Blog load failed"

# Generate initial sitemap
./manage.py ensure_sitemap

# Pull the blog every 10 minutes, and refresh the sitemap every 6 hours.
crontab - <<'EOF'
*/10 * * * * /app/manage.py load_blog >> /var/log/cron.log 2>&1
0 */6 * * * /app/manage.py ensure_sitemap >> /var/log/cron.log 2>&1
EOF

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