#!/bin/bash

# Renew certificates
docker compose run --rm certbot renew --quiet

# Reload NGINX to apply new certificates
docker compose exec nginx nginx -s reload