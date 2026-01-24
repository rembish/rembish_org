#!/bin/sh
# Entrypoint script for rembish.org frontend
# Substitutes environment variables in nginx config at runtime

set -e

# Substitute BACKEND_URL in nginx config
envsubst '${BACKEND_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Execute the main command
exec "$@"
