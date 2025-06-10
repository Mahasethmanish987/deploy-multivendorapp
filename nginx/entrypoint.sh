#!/bin/sh
set -e

# Replace DOMAIN placeholder in nginx.conf
envsubst '$DOMAIN' < /etc/nginx/nginx.conf > /etc/nginx/nginx.conf.tmp
mv /etc/nginx/nginx.conf.tmp /etc/nginx/nginx.conf

# Start Nginx in background for ACME challenge
nginx -g "daemon on;"

# Obtain SSL certificate if missing
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
  certbot certonly \
    --webroot \
    -w /var/www/certbot \
    -d $DOMAIN \
    --email $EMAIL \
    --non-interactive \
    --agree-tos
fi

# Stop background Nginx
nginx -s quit

# Start Nginx in foreground
exec nginx -g "daemon off;"