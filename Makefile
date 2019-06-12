PROJECT=ddr
APP=ddrpublic
USER=ddr
SHELL = /bin/bash

APP_VERSION := $(shell cat VERSION)
GIT_SOURCE_URL=https://github.com/densho/ddr-public

PYTHON_VERSION=python3.5

# Release name e.g. stretch
DEBIAN_CODENAME := $(shell lsb_release -sc)
# Release numbers e.g. 8.10
DEBIAN_RELEASE := $(shell lsb_release -sr)
# Sortable major version tag e.g. deb8
DEBIAN_RELEASE_TAG = deb$(shell lsb_release -sr | cut -c1)

# current branch name minus dashes or underscores
PACKAGE_BRANCH := $(shell git rev-parse --abbrev-ref HEAD | tr -d _ | tr -d -)
# current commit hash
PACKAGE_COMMIT := $(shell git log -1 --pretty="%h")
# current commit date minus dashes
PACKAGE_TIMESTAMP := $(shell git log -1 --pretty="%ad" --date=short | tr -d -)

# Media assets and Elasticsearch will be downloaded from this location.
# See https://github.com/densho/ansible-colo.git for more info:
# - templates/proxy/nginx.conf.j2
# - templates/static/nginx.conf.j2
PACKAGE_SERVER=ddr.densho.org/static/ddrpublic

SRC_REPO_NAMESDB=https://github.com/densho/namesdb.git

INSTALL_BASE=/opt
INSTALL_PUBLIC=$(INSTALL_BASE)/ddr-public
INSTALL_NAMESDB=./namesdb
REQUIREMENTS=./requirements.txt
PIP_CACHE_DIR=$(INSTALL_BASE)/pip-cache

VIRTUALENV=./venv/ddrpublic
SETTINGS=./ddrpublic/ddrpublic/settings.py

CONF_BASE=/etc/ddr
CONF_PRODUCTION=$(CONF_BASE)/ddrpublic.cfg
CONF_LOCAL=$(CONF_BASE)/ddrpublic-local.cfg

SQLITE_BASE=/var/lib/ddr
LOG_BASE=/var/log/ddr

MEDIA_BASE=/var/www/ddrpublic
MEDIA_ROOT=$(MEDIA_BASE)/media
STATIC_ROOT=$(MEDIA_BASE)/static

# Media assets are packaged in an "assets/" dir, *without the version*.
# The assets/ dir must be tgz'd into an $(ASSETS_TGZ) file
# and available for download from http://$(PACKAGE_SERVER)/$(ASSETS_TGZ).
# You can also place $(ASSETS_TGZ) in /tmp/$(ASSETS_VERSION)/$(ASSETS_TGZ).
ASSETS_VERSION=20170206
ASSETS_TGZ=ddr-public-assets-$(ASSETS_VERSION).tar.gz
ASSETS_INSTALL_DIR=$(MEDIA_BASE)/assets/$(ASSETS_VERSION)

ELASTICSEARCH=elasticsearch-2.4.6.deb

SUPERVISOR_GUNICORN_CONF=/etc/supervisor/conf.d/ddrpublic.conf
NGINX_CONF=/etc/nginx/sites-available/ddrpublic.conf
NGINX_CONF_LINK=/etc/nginx/sites-enabled/ddrpublic.conf

DEB_BRANCH := $(shell git rev-parse --abbrev-ref HEAD | tr -d _ | tr -d -)
DEB_ARCH=amd64
DEB_NAME_STRETCH=$(APP)-$(DEB_BRANCH)
# Application version, separator (~), Debian release tag e.g. deb8
# Release tag used because sortable and follows Debian project usage.
DEB_VERSION_STRETCH=$(APP_VERSION)~deb9
DEB_FILE_STRETCH=$(DEB_NAME_STRETCH)_$(DEB_VERSION_STRETCH)_$(DEB_ARCH).deb
DEB_VENDOR=Densho.org
DEB_MAINTAINER=<geoffrey.jost@densho.org>
DEB_DESCRIPTION=Densho Digital Repository site
DEB_BASE=opt/ddr-public


.PHONY: help


help:
	@echo "ddr-public Install Helper"
	@echo ""
	@echo "install - Does a complete install. Idempotent, so run as many times as you like."
	@echo "          IMPORTANT: Run 'adduser ddr' first to install ddr user and group."
	@echo "          Installation instructions: make howto-install"
	@echo "Subcommands:"
	@echo "    install-prep    - Various preperatory tasks"
	@echo "    install-daemons - Installs Nginx, Redis"
	@echo "    install-elasticsearch"
	@echo "    get-app         - Runs git-clone or git-pull on ddr-public"
	@echo "    install-app     - Just installer tasks for ddr-public"
	@echo "    install-static  - Downloads static media (Bootstrap, jquery, etc)"
	@echo ""
	@echo "test    - Run unit tests"
	@echo ""
	@echo "migrate - Initialize or update Django app's database tables."
	@echo ""
	@echo "branch BRANCH=[branch] - Switches ddr-public and supporting repos to [branch]."
	@echo ""
	@echo "reload  - Reloads supervisord and nginx configs"
	@echo "reload-nginx"
	@echo "reload-supervisors"
	@echo ""
	@echo "restart - Restarts all servers"
	@echo "restart-elasticsearch"
	@echo "restart-redis"
	@echo "restart-nginx"
	@echo "restart-supervisord"
	@echo ""
	@echo "status  - Server status"
	@echo ""
	@echo "uninstall - Deletes 'compiled' Python files. Leaves build dirs and configs."
	@echo "clean   - Deletes files created by building the program. Leaves configs."
	@echo ""
	@echo "More install info: make howto-install"

howto-install:
	@echo "HOWTO INSTALL"
	@echo "- Basic Debian netinstall"
	@echo "- edit /etc/network/interfaces"
	@echo "- reboot"
	@echo "- apt-get install openssh fail2ban ufw"
	@echo "- ufw allow 22/tcp"
	@echo "- ufw allow 80/tcp"
	@echo "- ufw enable"
	@echo "- apt-get install make"
	@echo "- adduser ddr"
	@echo "- git clone $(SRC_REPO_PUBLIC) $(INSTALL_PUBLIC)"
	@echo "- cd $(INSTALL_PUBLIC)/ddrpublic"
	@echo "- make install"
	@echo "- [make branch BRANCH=develop]"
	@echo "- [make install]"
	@echo "- Place copy of 'ddr' repo in $(DDR_REPO_BASE)/ddr."
	@echo "- make get-defs"
	@echo "- make migrate"
	@echo "- make restart"

help-all:
	@echo "install - Do a fresh install"
	@echo "install-prep    - git-config, add-user, apt-update, install-misc-tools"
	@echo "install-daemons - install-nginx install-redis install-elasticsearch"
	@echo "install-ddr     - install-ddr-public"
	@echo "install-static  - "
	@echo "update  - Do an update"
	@echo "restart - Restart servers"
	@echo "status  - Server status"
	@echo "install-configs - "
	@echo "update-ddr - "
	@echo "uninstall - "
	@echo "clean - "


get: get-ddr-public

install: install-prep get-app install-app install-daemons install-static install-configs

test: test-app

uninstall: uninstall-app uninstall-configs

clean: clean-app


install-prep: apt-update install-core git-config install-misc-tools

apt-update:
	@echo ""
	@echo "Package update ---------------------------------------------------------"
	apt-get --assume-yes update

apt-upgrade:
	@echo ""
	@echo "Package upgrade --------------------------------------------------------"
	apt-get --assume-yes upgrade

install-core:
	apt-get --assume-yes install bzip2 curl gdebi-core git-core logrotate ntp p7zip-full wget python3

git-config:
	git config --global alias.st status
	git config --global alias.co checkout
	git config --global alias.br branch
	git config --global alias.ci commit

install-misc-tools:
	@echo ""
	@echo "Installing miscellaneous tools -----------------------------------------"
	apt-get --assume-yes install ack-grep byobu elinks htop mg multitail


install-daemons: install-nginx install-redis

install-nginx:
	@echo ""
	@echo "Nginx ------------------------------------------------------------------"
	apt-get --assume-yes install nginx

install-redis:
	@echo ""
	@echo "Redis ------------------------------------------------------------------"
	apt-get --assume-yes install redis-server

install-elasticsearch:
	@echo ""
	@echo "Elasticsearch ----------------------------------------------------------"
# Elasticsearch is configured/restarted here so it's online by the time script is done.
	apt-get --assume-yes install openjdk-7-jre
	wget -nc -P /tmp/downloads http://$(PACKAGE_SERVER)/$(ELASTICSEARCH)
	gdebi --non-interactive /tmp/downloads/$(ELASTICSEARCH)
	cp $(INSTALLDIR)/conf/elasticsearch.yml /etc/elasticsearch/
	chown root.root /etc/elasticsearch/elasticsearch.yml
	chmod 644 /etc/elasticsearch/elasticsearch.yml
# 	@echo "${bldgrn}search engine (re)start${txtrst}"
	/etc/init.d/elasticsearch restart
	-mkdir -p /var/backups/elasticsearch
	chown -R elasticsearch.elasticsearch /var/backups/elasticsearch
	chmod -R 755 /var/backups/elasticsearch


install-virtualenv:
	@echo ""
	@echo "install-virtualenv -----------------------------------------------------"
	apt-get --assume-yes install python-pip python-virtualenv
	test -d $(VIRTUALENV) || virtualenv --python=python3 $(VIRTUALENV)


get-app: get-namesdb get-ddr-public

install-app: install-virtualenv install-namesdb install-ddr-public install-configs install-daemon-configs

test-app: test-ddr-public

uninstall-app: uninstall-namesdb uninstall-ddr-public uninstall-configs uninstall-daemon-configs

clean-app: clean-ddr-public


get-namesdb:
	@echo ""
	@echo "get-namesdb -----------------------------------------------------------"
	git status | grep "On branch"
	if test -d $(INSTALL_NAMESDB); \
	then cd $(INSTALL_NAMESDB) && git pull; \
	else cd $(INSTALL_PUBLIC) && git clone $(SRC_REPO_NAMESDB); \
	fi

setup-namesdb:
	git status | grep "On branch"
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_NAMESDB) && python setup.py install

install-namesdb: install-virtualenv
	@echo ""
	@echo "install-namesdb --------------------------------------------------------"
	git status | grep "On branch"
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_NAMESDB) && python setup.py install
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_NAMESDB) && pip3 install --cache-dir=$(PIP_CACHE_DIR) -U -r requirements.txt

uninstall-namesdb: install-virtualenv
	@echo ""
	@echo "uninstall-namesdb ------------------------------------------------------"
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_NAMESDB) && pip3 uninstall -y -r requirements.txt

clean-namesdb:
	-rm -Rf $(INSTALL_NAMESDB)/build
	-rm -Rf $(INSTALL_NAMESDB)/namesdb.egg-info
	-rm -Rf $(INSTALL_NAMESDB)/dist


get-ddr-public:
	@echo ""
	@echo "get-ddr-public ---------------------------------------------------------"
	git pull

install-ddr-public: clean-ddr-public
	@echo ""
	@echo "install-ddr-public -----------------------------------------------------"
	apt-get --assume-yes install imagemagick sqlite3 supervisor
	source $(VIRTUALENV)/bin/activate; \
	pip3 install --cache-dir=$(PIP_CACHE_DIR) -U -r $(INSTALL_PUBLIC)/requirements.txt
# logs dir
	-mkdir $(LOG_BASE)
	chown -R ddr.root $(LOG_BASE)
	chmod -R 755 $(LOG_BASE)
# sqlite db dir
	-mkdir $(SQLITE_BASE)
	chown -R ddr.root $(SQLITE_BASE)
	chmod -R 755 $(SQLITE_BASE)

test-ddr-public:
	@echo ""
	@echo "test-ddr-public --------------------------------------------------------"
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_PUBLIC); python ddrpublic/manage.py test ui --keepdb

uninstall-ddr-public:
	@echo ""
	@echo "uninstall-ddr-public ---------------------------------------------------"
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_PUBLIC)/ddrpublic && pip3 uninstall -y -r $(INSTALL_PUBLIC)/requirements.txt

clean-ddr-public:
	-rm -Rf $(INSTALL_PUBLIC)/ddrpublic/src


migrate:
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_PUBLIC)/ddrpublic && python manage.py migrate --noinput
	chown -R ddr.root $(SQLITE_BASE)
	chmod -R 750 $(SQLITE_BASE)
	chown -R ddr.root $(LOG_BASE)
	chmod -R 755 $(LOG_BASE)


install-static: get-ddrpublic-assets install-ddrpublic-assets install-restframework install-swagger

clean-static: clean-ddrpublic-assets clean-restframework clean-swagger

get-ddrpublic-assets:
	@echo ""
	@echo "get assets --------------------------------------------------------------"
	-mkdir -p /tmp/$(ASSETS_VERSION)
	wget -nc -P /tmp http://$(PACKAGE_SERVER)/$(ASSETS_TGZ)

install-ddrpublic-assets:
	@echo ""
	@echo "install assets ----------------------------------------------------------"
	rm -Rf $(ASSETS_INSTALL_DIR)
	-mkdir -p $(ASSETS_INSTALL_DIR)
	-mkdir -p /tmp/$(ASSETS_VERSION)
	tar xzf /tmp/$(ASSETS_TGZ) -C /tmp/$(ASSETS_VERSION)
	mv /tmp/$(ASSETS_VERSION)/assets/* $(ASSETS_INSTALL_DIR)

clean-ddrpublic-assets:
	@echo ""
	@echo "clean assets ------------------------------------------------------------"
	-rm -Rf $(ASSETS_INSTALL_DIR)
	-mkdir -p /tmp/$(ASSETS_VERSION)

install-restframework:
	@echo ""
	@echo "rest-framework assets ---------------------------------------------------"
	-mkdir -p $(MEDIA_BASE)
	cp -R $(VIRTUALENV)/lib/$(PYTHON_VERSION)/site-packages/rest_framework/static/rest_framework/ $(STATIC_ROOT)/

install-swagger:
	@echo ""
	@echo "rest-swagger assets -----------------------------------------------------"
	-mkdir -p $(MEDIA_BASE)
	cp -R $(VIRTUALENV)/lib/$(PYTHON_VERSION)/site-packages/drf_yasg/static/drf-yasg/ $(STATIC_ROOT)/

clean-restframework:
	-rm -Rf $(STATIC_ROOT)/rest_framework/

clean-swagger:
	-rm -Rf $(STATIC_ROOT)/drf_yasg/


install-configs:
	@echo ""
	@echo "configuring ddr-public -------------------------------------------------"
# base settings file
# /etc/ddr/ddrpublic.cfg must be readable by all
# /etc/ddr/ddrpublic-local.cfg must be readable by ddr but contains sensitive info
	-mkdir /etc/ddr
	cp $(INSTALL_PUBLIC)/conf/ddrpublic.cfg $(CONF_PRODUCTION)
	chown root.root $(CONF_PRODUCTION)
	chmod 644 $(CONF_PRODUCTION)
	touch $(CONF_LOCAL)
	chown ddr.root $(CONF_LOCAL)
	chmod 640 $(CONF_LOCAL)
# web app settings
	cp $(INSTALL_PUBLIC)/conf/settings.py $(SETTINGS)
	chown root.root $(SETTINGS)
	chmod 644 $(SETTINGS)

uninstall-configs:
	-rm $(SETTINGS)
	-rm $(CONF_PRODUCTION)
	-rm $(CONF_SECRET)


install-daemon-configs:
	@echo ""
	@echo "install-daemon-configs -------------------------------------------------"
# nginx settings
	cp $(INSTALL_PUBLIC)/conf/nginx.conf $(NGINX_CONF)
	chown root.root $(NGINX_CONF)
	chmod 644 $(NGINX_CONF)
	-ln -s $(NGINX_CONF) $(NGINX_CONF_LINK)
	-rm /etc/nginx/sites-enabled/default
# supervisord
	cp $(INSTALL_PUBLIC)/conf/supervisor.conf $(SUPERVISOR_GUNICORN_CONF)
	chown root.root $(SUPERVISOR_GUNICORN_CONF)
	chmod 644 $(SUPERVISOR_GUNICORN_CONF)

uninstall-daemon-configs:
	-rm $(NGINX_CONF)
	-rm $(NGINX_CONF_LINK)


reload: reload-nginx reload-supervisor

reload-nginx:
	/etc/init.d/nginx reload

reload-supervisor:
	supervisorctl reload

reload-app: reload-supervisor


stop: stop-redis stop-nginx stop-supervisor

stop-elasticsearch:
	/etc/init.d/elasticsearch stop

stop-redis:
	/etc/init.d/redis-server stop

stop-nginx:
	/etc/init.d/nginx stop

stop-supervisor:
	/etc/init.d/supervisor stop

stop-app:
	supervisorctl stop ddrpublic


restart: restart-redis restart-nginx restart-supervisor

restart-elasticsearch:
	/etc/init.d/elasticsearch restart

restart-redis:
	/etc/init.d/redis-server restart

restart-nginx:
	/etc/init.d/nginx restart

restart-supervisor:
	/etc/init.d/supervisor restart

restart-app:
	supervisorctl restart ddrpublic


# just Redis and Supervisor
restart-minimal: restart-redis stop-nginx restart-supervisor


status:
	@echo "------------------------------------------------------------------------"
	-/etc/init.d/elasticsearch status
	@echo " - - - - -"
	-/etc/init.d/redis-server status
	@echo " - - - - -"
	-/etc/init.d/nginx status
	@echo " - - - - -"
	-supervisorctl status
	@echo ""

git-status:
	@echo "------------------------------------------------------------------------"
	cd $(INSTALL_PUBLIC) && git status


# http://fpm.readthedocs.io/en/latest/
install-fpm:
	@echo "install-fpm ------------------------------------------------------------"
	apt-get install ruby ruby-dev rubygems build-essential
	gem install --no-ri --no-rdoc fpm

# https://stackoverflow.com/questions/32094205/set-a-custom-install-directory-when-making-a-deb-package-with-fpm
# https://brejoc.com/tag/fpm/
deb: deb-stretch

deb-stretch:
	@echo ""
	@echo "DEB packaging (stretch) ------------------------------------------------"
	-rm -Rf $(DEB_FILE_STRETCH)
	virtualenv --python=python3 --relocatable $(VIRTUALENV)  # Make venv relocatable
	fpm   \
	--verbose   \
	--input-type dir   \
	--output-type deb   \
	--name $(DEB_NAME_STRETCH)   \
	--version $(DEB_VERSION_STRETCH)   \
	--package $(DEB_FILE_STRETCH)   \
	--url "$(GIT_SOURCE_URL)"   \
	--vendor "$(DEB_VENDOR)"   \
	--maintainer "$(DEB_MAINTAINER)"   \
	--description "$(DEB_DESCRIPTION)"   \
	--depends "imagemagick"  \
	--depends "libxml2-dev"  \
	--depends "libxslt1-dev"  \
	--depends "libz-dev"  \
	--depends "nginx"   \
	--depends "python3"   \
	--depends "redis-server"   \
	--depends "sqlite3"  \
	--depends "supervisor"   \
	--after-install "bin/fpm-mkdir-log.sh"   \
	--chdir $(INSTALL_PUBLIC)   \
	conf/ddrpublic.cfg=etc/ddr/ddrpublic.cfg   \
	bin=$(DEB_BASE)   \
	conf=$(DEB_BASE)   \
	COPYRIGHT=$(DEB_BASE)   \
	ddrpublic=$(DEB_BASE)   \
	.git=$(DEB_BASE)   \
	.gitignore=$(DEB_BASE)   \
	INSTALL=$(DEB_BASE)   \
	LICENSE=$(DEB_BASE)   \
	Makefile=$(DEB_BASE)   \
	namesdb=$(DEB_BASE)   \
	README.rst=$(DEB_BASE)   \
	requirements.txt=$(DEB_BASE)   \
	venv=$(DEB_BASE)   \
	venv/ddrpublic/lib/$(PYTHON_VERSION)/site-packages/rest_framework/static/rest_framework=$(STATIC_ROOT)  \
	venv/ddrpublic/lib/$(PYTHON_VERSION)/site-packages/drf_yasg/static/=$(STATIC_ROOT)  \
	VERSION=$(DEB_BASE)
