FROM nginx:latest

# Create Certbot directories
RUN mkdir -p /var/www/certbot/.well-known/acme-challenge

# Copy custom NGINX config
COPY nginx.conf /etc/nginx/nginx.conf

# Expose HTTP & HTTPS
EXPOSE 80 443

# Run NGINX
CMD ["nginx", "-g", "daemon off;"]