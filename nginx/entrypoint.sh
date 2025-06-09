#!/bin/sh
set -e

# Create necessary directories
mkdir -p /var/www/certbot
mkdir -p /var/log/letsencrypt

# Always start Nginx first for webroot verification
echo "Starting Nginx temporarily for certificate setup..."
nginx -g 'daemon on;'  # Start in background

# Run certbot if certificate doesn't exist
if [ ! -f /etc/letsencrypt/live/foodonline.run.place/fullchain.pem ]; then
  echo "Obtaining SSL certificate using webroot method..."
  certbot certonly --webroot \
    --non-interactive \
    --agree-tos \
    --email mahasethmanish63@gmail.com \
    -d foodonline.run.place \
    -w /var/www/certbot \
    --logs-dir /var/log/letsencrypt \
    --work-dir /var/lib/letsencrypt
else
  echo "Certificate already exists. Skipping initial setup."
fi

# Stop temporary Nginx
echo "Stopping temporary Nginx..."
nginx -s stop

# Setup cron job
echo "PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin" > /etc/crontabs/root
echo "0 0 * * * certbot renew --webroot -w /var/www/certbot --quiet --post-hook 'nginx -s reload'" >> /etc/crontabs/root
chmod 0644 /etc/crontabs/root

# Start cron
crond -b -l 8

# Start main Nginx
echo "Starting production Nginx..."
exec nginx -g 'daemon off;'