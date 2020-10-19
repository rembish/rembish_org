FROM node:latest AS builder

COPY package.json ./
RUN npm install \
    && mkdir -p /vendor/icofont && mv node_modules/@icon/icofont/icofont.* /vendor/icofont \
    && mkdir -p /vendor/bootstrap/css && mkdir -p /vendor/bootstrap/js \
        && mv node_modules/bootstrap/dist/css/*.min.css /vendor/bootstrap/css \
        && mv node_modules/bootstrap/dist/js/*.min.js /vendor/bootstrap/js \
    && mkdir -p /vendor/boxicons/css && mkdir -p /vendor/boxicons/fonts \
        && mv node_modules/boxicons/css/*.min.css /vendor/boxicons/css \
        && mv node_modules/boxicons/fonts/* /vendor/boxicons/fonts \
    && mkdir -p /vendor/jquery && mv node_modules/jquery/dist/*.min.js /vendor/jquery

FROM nginx:latest

EXPOSE 80 443

WORKDIR /app
VOLUME /app/ssl
COPY nginx/rembish.conf.template /etc/nginx/templates/
COPY nginx/docker-entrypoint.sh /docker-entrypoint.sh
COPY rembish_org/static static/
COPY --from=builder /vendor static/vendor/
COPY dockerfiles/nginx.dockerfile /Dockerfile
