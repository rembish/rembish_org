FROM nginx:latest

EXPOSE 80 443

WORKDIR /app
VOLUME /app/ssl
COPY nginx/rembish.conf.template /etc/nginx/templates/
COPY rembish_org/static static/
