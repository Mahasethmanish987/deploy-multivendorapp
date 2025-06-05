FROM nginx:1.25-alpine

# Install dependencies
RUN apk update && \
    apk add --no-cache \
        certbot \
        openssl \
        tzdata \
        py3-pip \
        py3-cryptography \
        python3 \
        && \
    rm -rf /var/cache/apk/*

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom configuration
COPY nginx.conf /etc/nginx/conf.d/foodonline.conf

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create directory for certbot challenges
RUN mkdir -p /var/www/certbot && \
    chmod -R 755 /var/www/certbot

ENTRYPOINT ["/entrypoint.sh"]