
#!/bin/sh
set -e

# Create necessary directories (if they don't exist)
mkdir -p /var/www/certbot
mkdir -p /var/log/letsencrypt

# Run certbot if certificate doesn't exist
if [ ! -f /etc/letsencrypt/live/foodonline.run.place/fullchain.pem ]; then
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

# Setup cron job (Alpine-specific)
echo "Setting up daily certificate renewal..."
echo '0 0 * * * certbot renew --quiet --post-hook "nginx -s reload"' > /etc/>
# Set proper permissions for cron
chmod 0644 /etc/crontabs/root

# Start cron daemon in background
echo "Starting cron daemon..."
crond -b -l 8

# Start Nginx in foreground
echo "Starting Nginx..."
exec nginx -g 'daemon off;'