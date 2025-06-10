#!/bin/bash

set -e

# Start NGINX temporarily for Certbot validation
nginx

# Wait for NGINX to start
sleep 5

# Check if certificate already exists
if [ ! -f "/etc/letsencrypt/live/yourdomain.com/fullchain.pem" ]; then
    echo "Requesting Let's Encrypt certificate..."
    certbot certonly --webroot \
      --webroot-path=/var/www/certbot \
      --agree-tos \
      --no-eff-email \
      --email mahasethmanish63@gmail.com \
      -d foodonline.run.place \
      --non-interactive
else
    echo "Certificate already exists. Skipping Certbot."
fi

# Stop temporary NGINX instance
nginx -s stop

# Start NGINX in foreground
exec nginx -g 'daemon off;'
