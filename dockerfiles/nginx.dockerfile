FROM node:14-buster AS builder

COPY package.json ./
RUN npm install \
    && mkdir -p /vendor/bootstrap/css && mkdir -p /vendor/bootstrap/js \
        && mv node_modules/bootstrap/dist/css/*.min.css /vendor/bootstrap/css \
        && mv node_modules/bootstrap/dist/js/*.min.js /vendor/bootstrap/js \
    && mkdir -p /vendor/bootstrap-datepicker/css && mkdir -p /vendor/bootstrap-datepicker/js \
        && mkdir -p /vendor/bootstrap-datepicker/locales \
        && mv node_modules/bootstrap-datepicker/dist/css/*.min.css /vendor/bootstrap-datepicker/css \
        && mv node_modules/bootstrap-datepicker/dist/js/*.min.js /vendor/bootstrap-datepicker/js \
        && mv node_modules/bootstrap-datepicker/dist/locales/*.min.js /vendor/bootstrap-datepicker/locales \
    && mkdir -p /vendor/bootstrap-select/css && mkdir -p /vendor/bootstrap-select/js \
        && mv node_modules/bootstrap-select/dist/css/*.min.css /vendor/bootstrap-select/css \
        && mv node_modules/bootstrap-select/dist/js/*.min.js /vendor/bootstrap-select/js \
    && mkdir -p /vendor/bootstrap-timepicker/css && mkdir -p /vendor/bootstrap-timepicker/js \
        && mv node_modules/bootstrap-timepicker/css/*.min.css /vendor/bootstrap-timepicker/css \
        && mv node_modules/bootstrap-timepicker/js/*.min.js /vendor/bootstrap-timepicker/js \
    && mkdir -p /vendor/boxicons/css && mkdir -p /vendor/boxicons/fonts \
        && mv node_modules/boxicons/css/*.min.css /vendor/boxicons/css \
        && mv node_modules/boxicons/fonts/* /vendor/boxicons/fonts \
    && mkdir -p /vendor/flag-icon-css/css \
        && mv node_modules/flag-icon-css/css/*.min.css /vendor/flag-icon-css/css \
        && mv node_modules/flag-icon-css/flags /vendor/flag-icon-css/flags \
    && mkdir -p /vendor/icofont && mv node_modules/@icon/icofont/icofont.* /vendor/icofont \
    && mkdir -p /vendor/jquery && mv node_modules/jquery/dist/*.min.js /vendor/jquery \
    && mkdir -p /vendor/moment && mv node_modules/moment/min/*.min.js /vendor/moment \
    && mkdir -p /vendor/typed.js && mv node_modules/typed.js/lib/*.min.js /vendor/typed.js
COPY rembish_org/static/vendor/flaticon /vendor/flaticon/

FROM nginx:latest

EXPOSE 80 443

WORKDIR /app
VOLUME /app/ssl
COPY nginx/rembish.conf.template /etc/nginx/templates/
COPY nginx/docker-entrypoint.sh /docker-entrypoint.sh
COPY rembish_org/static static/
COPY --from=builder /vendor static/vendor/
COPY dockerfiles/nginx.dockerfile /Dockerfile
