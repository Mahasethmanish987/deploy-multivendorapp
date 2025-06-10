FROM nginx:1.25-alpine

# Copy configurations
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY entrypoint.sh /entrypoint.sh

# Install Certbot
RUN apk add --no-cache certbot && \
    chmod +x /entrypoint.sh

VOLUME ["/etc/letsencrypt", "/var/www/certbot"]

ENTRYPOINT ["/entrypoint.sh"]