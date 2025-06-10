#!/bin/sh

# Phase 1: Start temporary Nginx for certificate issuance
echo "Starting temporary Nginx for SSL setup..."
nginx -c /etc/nginx/nginx.conf

# Phase 2: Obtain SSL certificates
if [ ! -f /etc/letsencrypt/live/foodonline.run.place/fullchain.pem ]; then
    echo "No SSL certificates found. Obtaining new certificates..."
    
    # Verify challenge is accessible locally first
    echo "Verifying local challenge access..."
    touch /var/www/certbot/test.txt
    curl -f http://localhost/.well-known/acme-challenge/test.txt || exit 1
    
    certbot certonly --webroot -w /var/www/certbot \
        --email your-email@example.com --agree-tos --no-eff-email \
        -d foodonline.run.place \
        --non-interactive --force-renewal || { 
            echo "Certificate request failed"
            exit 1
        }
else
    echo "Existing SSL certificates found"
fi

# Phase 3: Stop temporary Nginx
echo "Stopping temporary Nginx..."
nginx -s quit
sleep 2

# Phase 4: Start final Nginx with SSL config
echo "Starting Nginx with SSL configuration..."
exec nginx -g "daemon off;"