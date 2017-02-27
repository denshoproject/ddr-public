SHELL = /bin/bash
DEBIAN_CODENAME := $(shell lsb_release -sc)

PACKAGE_SERVER=ddr.densho.org/static/ddrpublic

SRC_REPO_CMDLN=https://github.com/densho/ddr-cmdln.git
SRC_REPO_DEFS=https://github.com/densho/ddr-defs.git
SRC_REPO_MANUAL=https://github.com/densho/ddr-manual.git

INSTALL_BASE=/usr/local/src
INSTALL_CMDLN=$(INSTALL_BASE)/ddr-cmdln
INSTALL_PUBLIC=$(INSTALL_BASE)/ddr-public
INSTALL_DEFS=$(INSTALL_BASE)/ddr-defs
INSTALL_MANUAL=$(INSTALL_BASE)/ddr-manual

VIRTUALENV=$(INSTALL_BASE)/env/ddrpublic
SETTINGS=$(INSTALL_PUBLIC)/ddrpublic/ddrpublic/settings.py

CONF_BASE=/etc/ddr
CONF_DEFS=$(CONF_BASE)/ddr-defs
CONF_PRODUCTION=$(CONF_BASE)/ddrpublic.cfg
CONF_LOCAL=$(CONF_BASE)/ddrpublic-local.cfg
CONF_SECRET=$(CONF_BASE)/ddrpublic-secret-key.txt

SQLITE_BASE=/var/lib/ddr
LOG_BASE=/var/log/ddr

DDR_REPO_BASE=/var/www/media

MEDIA_BASE=/var/www/ddrpublic
MEDIA_ROOT=$(MEDIA_BASE)/media
STATIC_ROOT=$(MEDIA_BASE)/static

ELASTICSEARCH=elasticsearch-2.4.4.deb
MODERNIZR=modernizr-2.6.2.js
JQUERY=jquery-1.11.0.min.js
BOOTSTRAP=bootstrap-3.1.1-dist.zip
ASSETS_VERSION=20170206
ASSETS=ddr-public-assets-$(ASSETS_VERSION).tar.gz
ASSETS_BASE=$(MEDIA_BASE)/assets/$(ASSETS_VERSION)
# wget https://download.elastic.co/elasticsearch/elasticsearch/elasticsearch-2.4.4.deb
# wget http://code.jquery.com/jquery-1.11.0.min.js
# wget https://github.com/twbs/bootstrap/releases/download/v3.1.1/bootstrap-3.1.1-dist.zip

SUPERVISOR_GUNICORN_CONF=/etc/supervisor/conf.d/gunicorn_ddrpublic.conf
NGINX_CONF=/etc/nginx/sites-available/ddrpublic.conf
NGINX_CONF_LINK=/etc/nginx/sites-enabled/ddrpublic.conf


.PHONY: help


help:
	@echo "ddr-public Install Helper"
	@echo ""
	@echo "install - Does a complete install. Idempotent, so run as many times as you like."
	@echo "          IMPORTANT: Run 'adduser ddr' first to install ddr user and group."
	@echo "          Installation instructions: make howto-install"
	@echo "Subcommands:"
	@echo "    install-prep    - Various preperatory tasks"
	@echo "    install-daemons - Installs Nginx, Redis, Elasticsearch"
	@echo "    get-app         - Runs git-clone or git-pull on ddr-cmdln and ddr-public"
	@echo "    install-app     - Just installer tasks for ddr-cmdln and ddr-public"
	@echo "    install-static  - Downloads static media (Bootstrap, jquery, etc)"
	@echo ""
	@echo "get-ddr-defs - Installs ddr-defs in $(CONF_DEFS)."
	@echo ""
	@echo ""
	@echo "syncdb  - Initialize or update Django app's database tables."
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
	@echo "- make syncdb"
	@echo "- make restart"

help-all:
	@echo "install - Do a fresh install"
	@echo "install-prep    - git-config, add-user, apt-update, install-misc-tools"
	@echo "install-daemons - install-nginx install-redis install-elasticsearch"
	@echo "install-ddr     - install-ddr-cmdln install-ddr-public"
	@echo "install-static  - "
	@echo "update  - Do an update"
	@echo "restart - Restart servers"
	@echo "status  - Server status"
	@echo "install-configs - "
	@echo "update-ddr - "
	@echo "uninstall - "
	@echo "clean - "


get: get-ddr-cmdln get-ddr-public

install: install-prep get-app install-app install-daemons install-static install-configs

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
	cp $(INSTALLDIR)/debian/conf/elasticsearch.yml /etc/elasticsearch/
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
	test -d $(VIRTUALENV) || virtualenv --distribute --setuptools $(VIRTUALENV)

install-setuptools: install-virtualenv
	@echo ""
	@echo "install-setuptools -----------------------------------------------------"
	apt-get --assume-yes install python-dev
	source $(VIRTUALENV)/bin/activate; \
	pip install -U bpython setuptools


get-app: get-ddr-cmdln get-ddr-public get-ddr-manual

install-app: install-virtualenv install-setuptools install-ddr-cmdln install-ddr-public install-ddr-manual install-configs install-daemon-configs

uninstall-app: uninstall-ddr-cmdln uninstall-ddr-public uninstall-ddr-manual uninstall-configs uninstall-daemon-configs

clean-app: clean-ddr-cmdln clean-ddr-public clean-ddr-manual


get-ddr-cmdln:
	@echo ""
	@echo "get-ddr-cmdln ----------------------------------------------------------"
	if test -d $(INSTALL_CMDLN); \
	then cd $(INSTALL_CMDLN) && git pull; \
	else cd $(INSTALL_BASE) && git clone $(SRC_REPO_CMDLN); \
	fi

setup-ddr-cmdln:
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_CMDLN)/ddr && python setup.py install

install-ddr-cmdln: clean-ddr-cmdln
	@echo ""
	@echo "install-ddr-cmdln ------------------------------------------------------"
	apt-get --assume-yes install git-core git-annex libxml2-dev libxslt1-dev libz-dev pmount udisks
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_CMDLN)/ddr && python setup.py install
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_CMDLN)/ddr && pip install -U -r $(INSTALL_CMDLN)/ddr/requirements/production.txt
	-mkdir $(LOG_BASE)
	chown -R ddr.root $(LOG_BASE)
	chmod -R 755 $(LOG_BASE)
	-mkdir -p $(MEDIA_ROOT)
	chown -R ddr.root $(MEDIA_ROOT)
	chmod -R 755 $(MEDIA_ROOT)

uninstall-ddr-cmdln:
	@echo ""
	@echo "uninstall-ddr-cmdln ----------------------------------------------------"
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_CMDLN)/ddr && pip uninstall -y -r $(INSTALL_CMDLN)/ddr/requirements/production.txt
	-rm /usr/local/bin/ddr*
	-rm -Rf /usr/local/lib/python2.7/dist-packages/DDR*
	-rm -Rf /usr/local/lib/python2.7/dist-packages/ddr*

clean-ddr-cmdln:
	-rm -Rf $(INSTALL_CMDLN)/ddr/build


get-ddr-public:
	@echo ""
	@echo "get-ddr-public ---------------------------------------------------------"
	git pull

install-ddr-public: clean-ddr-public
	@echo ""
	@echo "install-ddr-public -----------------------------------------------------"
	apt-get --assume-yes install imagemagick sqlite3 supervisor
	source $(VIRTUALENV)/bin/activate; \
	pip install -U -r $(INSTALL_PUBLIC)/ddrpublic/requirements/production.txt
# ddr repo
	-mkdir -p $(DDR_REPO_BASE)
	chown -R ddr.root $(DDR_REPO_BASE)
	chmod -R 755 $(DDR_REPO_BASE)
# logs dir
	-mkdir $(LOG_BASE)
	chown -R ddr.root $(LOG_BASE)
	chmod -R 755 $(LOG_BASE)
# sqlite db dir
	-mkdir $(SQLITE_BASE)
	chown -R ddr.root $(SQLITE_BASE)
	chmod -R 755 $(SQLITE_BASE)

uninstall-ddr-public:
	@echo ""
	@echo "uninstall-ddr-public ---------------------------------------------------"
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_PUBLIC)/ddrpublic && pip uninstall -y -r $(INSTALL_PUBLIC)/ddrpublic/requirements/production.txt
	-rm /usr/local/lib/python2.7/dist-packages/ddrpublic-*
	-rm -Rf /usr/local/lib/python2.7/dist-packages/ddrpublic

clean-ddr-public:
	-rm -Rf $(INSTALL_PUBLIC)/ddrpublic/src


get-ddr-defs:
	@echo ""
	@echo "get-ddr-defs -----------------------------------------------------------"
	if test -d $(CONF_DEFS); \
	then cd $(CONF_DEFS) && git pull; \
	else cd $(CONF_BASE) && git clone $(SRC_REPO_DEFS) $(CONF_DEFS); \
	fi


syncdb:
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_PUBLIC)/ddrpublic && python manage.py syncdb --noinput
	chown -R ddr.root $(SQLITE_BASE)
	chmod -R 750 $(SQLITE_BASE)
	chown -R ddr.root $(LOG_BASE)
	chmod -R 755 $(LOG_BASE)

branch:
	cd $(INSTALL_PUBLIC)/ddrpublic; python ./bin/git-checkout-branch.py $(BRANCH)


install-static: get-ddrpublic-assets install-restframework

clean-static: clean-ddrpublic-assets clean-restframework

get-ddrpublic-assets:
	@echo ""
	@echo "get assets --------------------------------------------------------------"
	rm -Rf $(ASSETS_BASE)
	-mkdir -p $(ASSETS_BASE)
	-mkdir -p /tmp/$(ASSETS_VERSION)
	wget -nc -P /tmp http://$(PACKAGE_SERVER)/$(ASSETS)
	tar xzf /tmp/$(ASSETS) -C /tmp/$(ASSETS_VERSION)
	mv /tmp/$(ASSETS_VERSION)/assets/* $(ASSETS_BASE)

clean-ddrpublic-assets:
	-rm -Rf $(ASSETS_BASE)
	-mkdir -p /tmp/$(ASSETS_VERSION)

install-restframework:
	@echo ""
	@echo "rest_framework ----------------------------------------------------------"
	-mkdir -p $(MEDIA_BASE)
	cp -R /usr/local/src/env/ddrpublic/lib/python2.7/site-packages/rest_framework/static/rest_framework/ $(STATIC_ROOT)/

clean-restframework:
	-rm -Rf $(STATIC_ROOT)/rest_framework/


install-configs:
	@echo ""
	@echo "configuring ddr-public -------------------------------------------------"
# base settings file
# /etc/ddr/ddrpublic.cfg must be readable by all
# /etc/ddr/ddrpublic-local.cfg must be readable by ddr but contains sensitive info
	-mkdir /etc/ddr
	cp $(INSTALL_PUBLIC)/debian/conf/ddrpublic.cfg $(CONF_PRODUCTION)
	chown root.root $(CONF_PRODUCTION)
	chmod 644 $(CONF_PRODUCTION)
	touch $(CONF_LOCAL)
	chown ddr.root $(CONF_LOCAL)
	chmod 640 $(CONF_LOCAL)
	python -c 'import random; print "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)])' > $(CONF_SECRET)
	chown ddr.root $(CONF_SECRET)
	chmod 640 $(CONF_SECRET)
# web app settings
	cp $(INSTALL_PUBLIC)/debian/conf/settings.py $(SETTINGS)
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
	cp $(INSTALL_PUBLIC)/debian/conf/ddrpublic.conf $(NGINX_CONF)
	chown root.root $(NGINX_CONF)
	chmod 644 $(NGINX_CONF)
	-ln -s $(NGINX_CONF) $(NGINX_CONF_LINK)
	-rm /etc/nginx/sites-enabled/default
# supervisord
	cp $(INSTALL_PUBLIC)/debian/conf/gunicorn_ddrpublic.conf $(SUPERVISOR_GUNICORN_CONF)
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


stop: stop-elasticsearch stop-redis stop-nginx stop-supervisor

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
	cd $(INSTALL_CMDLN) && git status
	@echo "------------------------------------------------------------------------"
	cd $(INSTALL_PUBLIC) && git status


get-ddr-manual:
	@echo ""
	@echo "get-ddr-manual ---------------------------------------------------------"
	if test -d $(INSTALL_MANUAL); \
	then cd $(INSTALL_MANUAL) && git pull; \
	else cd $(INSTALL_BASE) && git clone $(SRC_REPO_MANUAL); \
	fi

install-ddr-manual:
	@echo ""
	@echo "install-ddr-manual -----------------------------------------------------"
	source $(VIRTUALENV)/bin/activate; \
	pip install -U sphinx
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_MANUAL) && make html
	rm -Rf $(MEDIA_ROOT)/manual
	mv $(INSTALL_MANUAL)/build/html $(MEDIA_ROOT)/manual

uninstall-ddr-manual:
	pip uninstall -y sphinx

clean-ddr-manual:
	-rm -Rf $(INSTALL_MANUAL)/build
