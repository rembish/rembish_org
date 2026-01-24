#!/bin/sh
# Entrypoint script for rembish.org frontend
# Substitutes environment variables in nginx config at runtime

set -e

# Extract hostname from BACKEND_URL (e.g., https://foo.run.app -> foo.run.app)
export BACKEND_HOST=$(echo "$BACKEND_URL" | sed 's|https://||' | sed 's|/.*||')

# Substitute variables in nginx config
envsubst '${BACKEND_URL} ${BACKEND_HOST}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Execute the main command
exec "$@"
