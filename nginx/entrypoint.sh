#!/bin/sh
set -e

# Create necessary directories
mkdir -p /var/www/certbot
mkdir -p /var/log/letsencrypt

# Run certbot if certificate doesn't exist
if [ ! -f /etc/letsencrypt/live/foodonline.run.place/fullchain.pem ]; then
  echo "Stopping Nginx for initial certificate setup..."
  nginx -s stop || true
  
  echo "Obtaining SSL certificate..."
  certbot certonly --standalone \
    --non-interactive \
    --agree-tos \
    --email mahasethmanish63@gmail.com \
    -d foodonline.run.place \
    --logs-dir /var/log/letsencrypt \
    --work-dir /var/lib/letsencrypt
else
  echo "Certificate already exists. Skipping initial setup."
fi

# Setup cron job with PATH
echo "PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin" > /etc/crontabs/root
echo "0 0 * * * certbot renew --webroot -w /var/www/certbot --quiet --post-hook 'nginx -s reload'" >> /etc/crontabs/root
chmod 0644 /etc/crontabs/root

# Start cron daemon in background
echo "Starting cron daemon..."
crond -b -l 8

# Start Nginx in foreground
echo "Starting Nginx..."
exec nginx -g 'daemon off;'