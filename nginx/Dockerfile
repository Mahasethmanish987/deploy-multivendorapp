FROM nginx:alpine

# Create directory for Certbot challenge files
# This ensures the directory exists even if volumes aren't mounted
RUN mkdir -p /var/www/certbot/.well-known/acme-challenge

# Copy your custom NGINX configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose HTTP (80) and HTTPS (443) ports
EXPOSE 80 443

# Start NGINX in foreground mode
CMD ["nginx", "-g", "daemon off;"]