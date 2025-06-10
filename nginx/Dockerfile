# nginx/Dockerfile

FROM nginx:latest

# Install Certbot
RUN apt-get update && \
    apt-get install -y certbot && \
    apt-get clean

# Create directories
RUN mkdir -p /var/www/certbot/.well-known/acme-challenge

# Copy custom NGINX config and entrypoint
COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Expose HTTP and HTTPS
EXPOSE 80 443

ENTRYPOINT ["/entrypoint.sh"]
