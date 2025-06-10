FROM nginx:latest

# Install Certbot (optional, but useful for manual renewals)
RUN apt-get update && \
    apt-get install -y certbot python3-certbot-nginx && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create required Certbot directories
RUN mkdir -p /var/www/certbot/.well-known/acme-challenge

# Copy custom NGINX config (if needed)
COPY nginx.conf /etc/nginx/nginx.conf

# Expose HTTP & HTTPS
EXPOSE 80 443

# Default command (just run NGINX)
CMD ["nginx", "-g", "daemon off;"]