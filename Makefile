PROJECT=ddr
APP=ddrpublic
USER=ddr
SHELL = /bin/bash

RUNSERVER_PORT=8001

APP_VERSION := $(shell cat VERSION)
GIT_SOURCE_URL=https://github.com/densho/ddr-public

# Release name e.g. stretch
DEBIAN_CODENAME := $(shell lsb_release -sc)
# Release numbers e.g. 8.10
DEBIAN_RELEASE := $(shell lsb_release -sr)
# Sortable major version tag e.g. deb8
DEBIAN_RELEASE_TAG = deb$(shell lsb_release -sr | cut -c1)

ifeq ($(DEBIAN_CODENAME), buster)
	PYTHON_VERSION=python3.7
endif
ifeq ($(DEBIAN_CODENAME), bullseye)
	PYTHON_VERSION=python3.9
endif

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

SRC_REPO_NAMESDB=https://github.com/densho/namesdb
SRC_REPO_IREIZO=https://github.com/denshoproject/ireizo-public.git
SRC_REPO_ASSETS=https://github.com/denshoproject/ddr-public-assets.git

INSTALL_BASE=/opt
INSTALL_PUBLIC=$(INSTALL_BASE)/ddr-public
INSTALL_NAMESDB=./namesdb
INSTALL_IREIZO=$(INSTALL_BASE)/ireizo-public
INSTALL_ASSETS=/opt/ddr-public-assets
REQUIREMENTS=./requirements.txt
PIP_CACHE_DIR=$(INSTALL_BASE)/pip-cache

VIRTUALENV=$(INSTALL_PUBLIC)/venv/ddrpublic

CONF_BASE=/etc/ddr
CONF_PRODUCTION=$(CONF_BASE)/ddrpublic.cfg
CONF_LOCAL=$(CONF_BASE)/ddrpublic-local.cfg

SQLITE_BASE=/var/lib/ddr
LOG_BASE=/var/log/ddr

MEDIA_BASE=/var/www/ddrpublic
MEDIA_ROOT=$(MEDIA_BASE)/media
ASSETS_ROOT=$(MEDIA_BASE)/assets
STATIC_ROOT=$(MEDIA_BASE)/static

OPENJDK_PKG=
ifeq ($(DEBIAN_CODENAME), buster)
	OPENJDK_PKG=openjdk-11-jre-headless
endif
ifeq ($(DEBIAN_CODENAME), bullseye)
	OPENJDK_PKG=openjdk-17-jre-headless
endif

ELASTICSEARCH=elasticsearch-7.3.1-amd64.de

SUPERVISOR_GUNICORN_CONF=/etc/supervisor/conf.d/ddrpublic.conf
NGINX_CONF=/etc/nginx/sites-available/ddrpublic.conf
NGINX_CONF_LINK=/etc/nginx/sites-enabled/ddrpublic.conf

TGZ_BRANCH := $(shell python3 bin/package-branch.py)
TGZ_FILE=$(APP)_$(APP_VERSION)
TGZ_DIR=$(INSTALL_PUBLIC)/$(TGZ_FILE)
TGZ_PUBLIC=$(TGZ_DIR)/ddr-public
TGZ_NAMES=$(TGZ_DIR)/ddr-public/namesdb
TGZ_IREIZO=$(TGZ_DIR)/ireizo-public/
TGZ_ASSETS=$(TGZ_DIR)/ddr-public/ddr-public-assets

# Adding '-rcN' to VERSION will name the package "ddrlocal-release"
# instead of "ddrlocal-BRANCH"
DEB_BRANCH := $(shell python3 bin/package-branch.py)
DEB_ARCH=amd64
DEB_NAME_BUSTER=$(APP)-$(DEB_BRANCH)
DEB_NAME_BULLSEYE=$(APP)-$(DEB_BRANCH)
# Application version, separator (~), Debian release tag e.g. deb8
# Release tag used because sortable and follows Debian project usage.
DEB_VERSION_BUSTER=$(APP_VERSION)~deb10
DEB_VERSION_BULLSEYE=$(APP_VERSION)~deb11
DEB_FILE_BUSTER=$(DEB_NAME_BUSTER)_$(DEB_VERSION_BUSTER)_$(DEB_ARCH).deb
DEB_FILE_BULLSEYE=$(DEB_NAME_BULLSEYE)_$(DEB_VERSION_BULLSEYE)_$(DEB_ARCH).deb
DEB_VENDOR=Densho.org
DEB_MAINTAINER=<geoffrey.jost@densho.org>
DEB_DESCRIPTION=Densho Digital Repository site
DEB_BASE=opt/ddr-public


.PHONY: help


help:
	@echo "ddr-public Install Helper"
	@echo ""
	@echo "Most commands have subcommands (ex: install-ddr-cmdln, restart-supervisor)"
	@echo ""
	@echo "get     - Clones ddr-public, wgets static files & ES pkg."
	@echo "install - Performs complete install. See also: make howto-install"
	@echo "test    - Run unit tests"
	@echo ""
	@echo "migrate - Init/update Django app's database tables."
	@echo ""
	@echo "branch BRANCH=[branch] - Switches ddr-public and supporting repos to [branch]."
	@echo ""
	@echo "deb       - Makes a DEB package install file."
	@echo "remove    - Removes Debian packages for dependencies."
	@echo "uninstall - Deletes 'compiled' Python files. Leaves build dirs and configs."
	@echo "clean     - Deletes files created while building app, leaves configs."
	@echo ""

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
	@echo "- make migrate"
	@echo "- make restart"



get: get-ddr-public

install: install-prep get-app install-app install-daemons install-configs

test: test-app

coverage: coverage-app

uninstall: uninstall-app uninstall-configs

clean: clean-app


install-prep: ddr-user install-core git-config install-misc-tools

ddr-user:
	-addgroup --gid=1001 ddr
	-adduser --uid=1001 --gid=1001 --home=/home/ddr --shell=/bin/bash --disabled-login --gecos "" ddr
	-addgroup ddr plugdev
	-addgroup ddr vboxsf
	printf "\n\n# ddrlocal: Activate virtualnv on login\nsource $(VIRTUALENV)/bin/activate\n" >> /home/ddr/.bashrc; \

install-core:
	apt-get --assume-yes install bzip2 curl gdebi-core git-core logrotate ntp p7zip-full wget

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
	apt-get --assume-yes remove apache2
	apt-get --assume-yes install nginx-light

remove-nginx:
	apt-get --assume-yes remove nginx-light

install-redis:
	@echo ""
	@echo "Redis ------------------------------------------------------------------"
	apt-get --assume-yes install redis-server

remove-redis:
	apt-get --assume-yes remove redis-server


get-elasticsearch:
	wget -nc -P /tmp/downloads http://$(PACKAGE_SERVER)/$(ELASTICSEARCH)

install-elasticsearch: install-core
	@echo ""
	@echo "Elasticsearch ----------------------------------------------------------"
# Elasticsearch is configured/restarted here so it's online by the time script is done.
	apt-get --assume-yes install $(OPENJDK_PKG)
	-gdebi --non-interactive /tmp/downloads/$(ELASTICSEARCH)
#cp $(INSTALL_LOCAL)/conf/elasticsearch.yml /etc/elasticsearch/
#chown root.root /etc/elasticsearch/elasticsearch.yml
#chmod 644 /etc/elasticsearch/elasticsearch.yml
# 	@echo "${bldgrn}search engine (re)start${txtrst}"
	-service elasticsearch stop
	-systemctl disable elasticsearch.service

enable-elasticsearch:
	systemctl enable elasticsearch.service

disable-elasticsearch:
	systemctl disable elasticsearch.service

remove-elasticsearch:
	apt-get --assume-yes remove $(OPENJDK_PKG) elasticsearch


install-virtualenv:
	@echo ""
	@echo "install-virtualenv -----------------------------------------------------"
	apt-get --assume-yes install python3-pip python3-venv
	python3 -m venv --system-site-packages $(VIRTUALENV)
	source $(VIRTUALENV)/bin/activate; \
	pip3 install -U --cache-dir=$(PIP_CACHE_DIR) pip

 install-setuptools: install-virtualenv
	@echo ""
	@echo "install-setuptools -----------------------------------------------------"
	apt-get --assume-yes install python3-dev
	source $(VIRTUALENV)/bin/activate; \
	pip3 install -U --cache-dir=$(PIP_CACHE_DIR) setuptools

get-app: get-namesdb get-ddr-public get-ireizo-public

install-app: install-virtualenv install-namesdb install-ireizo-public install-ddr-public install-configs install-daemon-configs

test-app: test-ddr-public

uninstall-app: uninstall-namesdb uninstall-ireizo-public uninstall-ddr-public uninstall-configs uninstall-daemon-configs

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


get-ireizo-public:
	@echo ""
	@echo "get-ireizo-public ------------------------------------------------------"
	git status | grep "On branch"
	if test -d $(INSTALL_IREIZO); \
	then cd $(INSTALL_IREIZO) && git pull; \
	else cd $(INSTALL_BASE) && git clone $(SRC_REPO_IREIZO); \
	fi

install-ireizo-public: install-virtualenv
	@echo ""
	@echo "install-ireizo-public --------------------------------------------------"
	-rm -Rf $(INSTALL_PUBLIC)/ddrpublic/ireizo_public
	-ln -s $(INSTALL_IREIZO)/ireizo_public $(INSTALL_PUBLIC)/ddrpublic/ireizo_public
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_IREIZO) && pip3 install --cache-dir=$(PIP_CACHE_DIR) -U -r requirements.txt

uninstall-ireizo-public: install-virtualenv
	@echo ""
	@echo "uninstall-ireizo-public ------------------------------------------------"
	-rm -Rf $(INSTALL_PUBLIC)/ddrpublic/ireizo_public

clean-ireizo-public:
	-rm -Rf $(INSTALL_IREIZO)/build
	-rm -Rf $(INSTALL_IREIZO)/namesdb.egg-info
	-rm -Rf $(INSTALL_IREIZO)/dist


get-ddr-public:
	@echo ""
	@echo "get-ddr-public ---------------------------------------------------------"
	git pull

install-ddr-public: install-setuptools mkdir-ddr-public
	@echo ""
	@echo "install-ddr-public -----------------------------------------------------"
	apt-get --assume-yes install  \
	imagemagick                   \
	bpython3                      \
	python3                       \
	python3-git                   \
	python3-redis                 \
	python3-requests              \
	sqlite3                       \
	supervisor
	source $(VIRTUALENV)/bin/activate; \
	pip3 install -U --cache-dir=$(PIP_CACHE_DIR) -r $(INSTALL_PUBLIC)/requirements.txt
	sudo -u ddr git config --global --add safe.directory $(INSTALL_PUBLIC)
	sudo -u ddr git config --global --add safe.directory $(INSTALL_NAMESDB)

install-test:
	@echo ""
	@echo "install-test ------------------------------------------------------------"
	apt-get --assume-yes install  \
	python3-coverage              \
	python3-pytest                \
	python3-pytest-cov            \
	python3-pytest-django         \
	python3-pytest-xdist
	source $(VIRTUALENV)/bin/activate; \
	pip3 install -U --cache-dir=$(PIP_CACHE_DIR) -r $(INSTALL_PUBLIC)/requirements-dev.txt

mkdir-ddr-public:
	@echo ""
	@echo "mkdir-ddr-public --------------------------------------------------------"
# logs dir
	-mkdir $(LOG_BASE)
	chown -R ddr.ddr $(LOG_BASE)
	chmod -R 775 $(LOG_BASE)
# sqlite db dir
	-mkdir $(SQLITE_BASE)
	chown -R ddr.ddr $(SQLITE_BASE)
	chmod -R 775 $(SQLITE_BASE)
# media dir
	-mkdir -p $(MEDIA_BASE)
	-mkdir -p $(MEDIA_ROOT)
	chown -R ddr.ddr $(MEDIA_ROOT)
	chmod -R 755 $(MEDIA_ROOT)

test-ddr-public: test-ddr-public-ui test-ddr-public-names

test-ddr-public-ui:
	@echo ""
	@echo "test-ddr-public-ui ----------------------------------------"
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_PUBLIC); python ddrpublic/manage.py test ui

test-ddr-public-names:
	@echo ""
	@echo "test-ddr-public-names ----------------------------------------"
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_PUBLIC); python ddrpublic/manage.py test names

shell:
	source $(VIRTUALENV)/bin/activate; \
	python ddrpublic/manage.py shell

runserver:
	source $(VIRTUALENV)/bin/activate; \
	python ddrpublic/manage.py runserver 0.0.0.0:$(RUNSERVER_PORT)

uninstall-ddr-public: install-setuptools
	@echo ""
	@echo "uninstall-ddr-public ---------------------------------------------------"
	source $(VIRTUALENV)/bin/activate; \
	pip3 uninstall -y -r $(INSTALL_PUBLIC)/requirements.txt

clean-ddr-public:
	-rm -Rf $(VIRTUALENV)
	-rm -Rf *.deb


get-ddr-public-assets:
	@echo ""
	@echo "get-ddr-public-assets --------------------------------------------------"
	if test -d $(INSTALL_ASSETS); \
	then cd $(INSTALL_ASSETS) && git pull; \
	else cd $(INSTALL_PUBLIC) && git clone $(SRC_REPO_ASSETS); \
	fi


migrate:
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_PUBLIC)/ddrpublic && python manage.py migrate --noinput
	chown -R ddr.ddr $(SQLITE_BASE)
	chmod -R 770 $(SQLITE_BASE)
	chown -R ddr.ddr $(LOG_BASE)
	chmod -R 775 $(LOG_BASE)


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


tgz-local:
	rm -Rf $(TGZ_DIR)
	git clone $(INSTALL_PUBLIC) $(TGZ_PUBLIC)
	git clone $(INSTALL_NAMESDB) $(TGZ_NAMES)
	git clone $(INSTALL_IREIZO) $(TGZ_IREIZO)
	git clone $(INSTALL_ASSETS) $(TGZ_ASSETS)
	cd $(TGZ_PUBLIC); git checkout develop; git checkout master
	cd $(TGZ_NAMES); git checkout develop; git checkout master
	cd $(TGZ_IREIZO); git checkout develop; git checkout master
	cd $(TGZ_ASSETS); git checkout develop; git checkout master
	tar czf $(TGZ_FILE).tgz $(TGZ_FILE)
	rm -Rf $(TGZ_DIR)


tgz:
	rm -Rf $(TGZ_DIR)
	git clone $(GIT_SOURCE_URL) $(TGZ_PUBLIC)
	git clone $(SRC_REPO_NAMESDB) $(TGZ_NAMES)
	git clone $(SRC_REPO_IREIZO) $(TGZ_IREIZO)
	git clone $(SRC_REPO_ASSETS) $(TGZ_ASSETS)
	cd $(TGZ_PUBLIC); git checkout develop; git checkout master
	cd $(TGZ_NAMES); git checkout develop; git checkout master
	cd $(TGZ_IREIZO); git checkout develop; git checkout master
	cd $(TGZ_ASSETS); git checkout develop; git checkout master
	tar czf $(TGZ_FILE).tgz $(TGZ_FILE)
	rm -Rf $(TGZ_DIR)


# http://fpm.readthedocs.io/en/latest/
install-fpm:
	@echo "install-fpm ------------------------------------------------------------"
	apt-get install --assume-yes ruby ruby-dev rubygems build-essential
	gem install --no-ri --no-rdoc fpm

# https://stackoverflow.com/questions/32094205/set-a-custom-install-directory-when-making-a-deb-package-with-fpm
# https://brejoc.com/tag/fpm/
deb: deb-bullseye

deb-buster:
	@echo ""
	@echo "DEB packaging (buster) -------------------------------------------------"
	-rm -Rf $(DEB_FILE_BUSTER)
# Make package
	fpm   \
	--verbose   \
	--input-type dir   \
	--output-type deb   \
	--name $(DEB_NAME_BUSTER)   \
	--version $(DEB_VERSION_BUSTER)   \
	--package $(DEB_FILE_BUSTER)   \
	--url "$(GIT_SOURCE_URL)"   \
	--vendor "$(DEB_VENDOR)"   \
	--maintainer "$(DEB_MAINTAINER)"   \
	--description "$(DEB_DESCRIPTION)"   \
	--depends "imagemagick"  \
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
	../ireizo-public=opt   \
	LICENSE=$(DEB_BASE)   \
	Makefile=$(DEB_BASE)   \
	namesdb=$(DEB_BASE)   \
	README.rst=$(DEB_BASE)   \
	requirements.txt=$(DEB_BASE)   \
	venv=$(DEB_BASE)   \
	VERSION=$(DEB_BASE)

deb-bullseye:
	@echo ""
	@echo "DEB packaging (bullseye) -------------------------------------------------"
	-rm -Rf $(DEB_FILE_BULLSEYE)
# Make package
	fpm   \
	--verbose   \
	--input-type dir   \
	--output-type deb   \
	--name $(DEB_NAME_BULLSEYE)   \
	--version $(DEB_VERSION_BULLSEYE)   \
	--package $(DEB_FILE_BULLSEYE)   \
	--url "$(GIT_SOURCE_URL)"   \
	--vendor "$(DEB_VENDOR)"   \
	--maintainer "$(DEB_MAINTAINER)"   \
	--description "$(DEB_DESCRIPTION)"   \
	--depends "imagemagick"  \
	--depends "nginx"  \
	--depends "bpython3"  \
	--depends "python3"  \
	--depends "python3-git"  \
	--depends "python3-redis"  \
	--depends "python3-requests"  \
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
	../ireizo-public=opt   \
	LICENSE=$(DEB_BASE)   \
	Makefile=$(DEB_BASE)   \
	namesdb=$(DEB_BASE)   \
	README.rst=$(DEB_BASE)   \
	requirements.txt=$(DEB_BASE)   \
	venv=$(DEB_BASE)   \
	VERSION=$(DEB_BASE)
