#! /usr/bin/make -f
PROJECT := rembish_org

SSL_PATH ?= $(CURDIR)/ssl
DEV_DOMAIN ?= dev.rembish.org

help:  ## This help dialog.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

devssl:  ## Generate self-signed dev certificates
	mkdir -p $(SSL_PATH)
	openssl req -x509 -newkey rsa:4096 -nodes -out $(SSL_PATH)/$(DEV_DOMAIN).crt -keyout $(SSL_PATH)/$(DEV_DOMAIN).key -days 365 -subj '/CN=$(DEV_DOMAIN)'
