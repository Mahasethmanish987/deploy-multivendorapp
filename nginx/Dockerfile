FROM nginx:alpine

# Install Certbot and OpenSSL
RUN apk add --no-cache certbot openssl

# Create directories for Certbot challenges and certificates
RUN mkdir -p /var/www/certbot && \
    mkdir -p /etc/letsencrypt

# Copy configurations and scripts
COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /entrypoint.sh

# Make entrypoint executable
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]