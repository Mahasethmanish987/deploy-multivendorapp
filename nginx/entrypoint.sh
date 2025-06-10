#!/bin/sh

# Phase 1: Start temporary Nginx for certificate issuance
echo "Starting temporary Nginx for SSL setup..."
nginx -c /etc/nginx/nginx.conf

# Wait for web service to be ready
echo "Waiting for web service to be ready..."
while ! curl -s http://web:8000 >/dev/null; do
    sleep 5
    echo "Still waiting for web service..."
done

# Phase 2: Obtain SSL certificates
if [ ! -f /etc/letsencrypt/live/foodonline.run.place/fullchain.pem ]; then
    echo "No SSL certificates found. Obtaining new certificates..."
    certbot certonly --webroot -w /var/www/certbot \
        --email your-email@example.com --agree-tos --no-eff-email \
        -d foodonline.run.place \
        --non-interactive || echo "Certificate request failed"
else
    echo "Existing SSL certificates found"
fi

# Phase 3: Stop temporary Nginx
echo "Stopping temporary Nginx..."
nginx -s quit
sleep 2

# Phase 4: Start final Nginx with SSL config
echo "Starting Nginx with SSL configuration..."
nginx -g "daemon off;"