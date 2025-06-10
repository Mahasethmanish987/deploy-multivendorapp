#!/bin/sh
set -x  # Enable command echoing for debugging
exec > /var/log/entrypoint.log 2>&1  # Log all output
DOMAIN="${DOMAIN:-foodonline.run.place}"
EMAIL="${EMAIL:-mahasethmanish63@gmail.com}" 
WEBROOT_PATH="/var/www/certbot" 
SSL_DIR="/etc/letsencrypt/live/$DOMAIN"

start_temp_nginx() {
    echo "Starting temporary HTTP server..."
    nginx -g "daemon on;"
}

# Stop temporary HTTP server
stop_temp_nginx() {
    echo "Stopping temporary HTTP server..."
    nginx -s quit
}

request_initial_cert() {
    echo "Requesting initial certificate for $DOMAIN"
    certbot certonly --webroot -w "$WEBROOT_PATH" \
        -d "$DOMAIN" \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL" \
        --rsa-key-size 4096 \
        --force-renewal  # Ensure new certs even if testing
}

renew_certs() {
    echo "Checking for certificate renewals..."
    certbot renew --webroot -w "$WEBROOT_PATH" \
        --non-interactive \
        --agree-tos \
        --rsa-key-size 4096
}

set_permissions() {
    echo "Setting permissions..."
    chown -R nginx:nginx "$WEBROOT_PATH"
    chmod -R 755 "$WEBROOT_PATH"
    chown -R nginx:nginx /etc/letsencrypt
    chmod -R 755 /etc/letsencrypt
}

mkdir -p "$WEBROOT_PATH/.well-known/acme-challenge"
set_permissions

# Phase 1: Start temporary HTTP server
start_temp_nginx

# Phase 2: Certificate management
if [ ! -f "$SSL_DIR/fullchain.pem" ]; then
    echo "Certificate not found - initial setup required"
    request_initial_cert
else
    echo "Existing certificates found"
    renew_certs
fi

stop_temp_nginx

# Phase 4: Start production server
echo "Starting production Nginx with SSL..."
exec nginx -g "daemon off;"