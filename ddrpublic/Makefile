SHELL = /bin/bash

PACKAGE_SERVER=tank.densho.org

INSTALL_BASE=/usr/local/src
INSTALLDIR=$(INSTALL_BASE)/ddr-public
PIP_CACHE_DIR=$(INSTALL_BASE)/pip-cache
VIRTUALENV=$(INSTALL_BASE)/env/ddrpublic

DDR_REPO_BASE=/var/www/media

MEDIA_BASE=/var/www/ddrpublic
MEDIA_ROOT=$(MEDIA_BASE)/media
STATIC_ROOT=$(MEDIA_BASE)/static

ELASTICSEARCH=elasticsearch-1.0.1.deb
MODERNIZR=modernizr-2.6.2.js
JQUERY=jquery-1.11.0.min.js
BOOTSTRAP=bootstrap-3.1.1-dist.zip
ASSETS=ddr-public-assets.tar.gz
# wget https://github.com/twbs/bootstrap/releases/download/v3.1.1/bootstrap-3.1.1-dist.zip
# wget http://code.jquery.com/jquery-1.11.0.min.js
# wget https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.0.1.deb

.PHONY: help


help:
	@echo "ddr-public Install Helper"
	@echo ""
	@echo "install - Does a complete install. Idempotent, so run as many times as you like."
	@echo "          IMPORTANT: Run 'adduser ddr' first to install ddr user and group."
	@echo "          Installation instructions: make howto-install"
	@echo ""
	@echo "syncdb  - Initialize or update Django app's database tables."
	@echo ""
	@echo "update  - Updates ddr-cmd and ddr-public and re-copies config files."
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

howto-install:
	@echo "HOWTO INSTALL"
	@echo "- Basic Debian netinstall"
	@echo "- # vi /etc/network/interfaces"
	@echo "- # reboot"
	@echo "- # apt-get install openssh fail2ban ufw"
	@echo "- # ufw allow 22/tcp"
	@echo "- # ufw allow 80/tcp"
	@echo "- # ufw enable"
	@echo "- # apt-get install make"
	@echo "- # adduser ddr"
	@echo "- # git clone https://github.com/densho/ddr-public.git $(INSTALLDIR)"
	@echo "- # cd $(INSTALLDIR)/ddrpublic"
	@echo "- # make install"
	@echo "- [Install ddr repo (must be done manually)]"
	@echo "- [Confirm that ddr-cmdln,ddr-local, and ddr repo are on correct branches]"
	@echo "- # make syncdb"
	@echo "- # make restart"



install: install-prep install-daemons install-ddr install-static install-configs

update: update-ddr

uninstall: uninstall-ddr

clean: clean-ddr


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


install-daemons: install-nginx install-redis install-elasticsearch

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
	apt-get --assume-yes install python-pip python-virtualenv
	test -d $(VIRTUALENV) || virtualenv --distribute --setuptools $(VIRTUALENV)

install-setuptools: install-virtualenv
	@echo ""
	@echo "install-setuptools -----------------------------------------------------"
	apt-get --assume-yes install python-dev
	source $(VIRTUALENV)/bin/activate; \
	pip install -U --download-cache=$(PIP_CACHE_DIR) bpython setuptools


install-ddr: install-ddr-cmdln install-ddr-local install-ddr-public

update-ddr: update-ddr-cmdln update-ddr-local update-ddr-public install-configs

uninstall-ddr: uninstall-ddr-cmdln uninstall-ddr-local uninstall-ddr-manual

clean-ddr: clean-ddr-cmdln clean-ddr-local clean-ddr-manual


install-ddr-cmdln: install-virtualenv install-setuptools
	@echo ""
	@echo "ddr-cmdln --------------------------------------------------------------"
	apt-get --assume-yes install git-core git-annex libexempi3 libxml2-dev libxslt1-dev libz-dev pmount udisks python-dev

	if test -d $(INSTALL_BASE)/ddr-cmdln; \
	then cd $(INSTALL_BASE)/ddr-cmdln && git pull; \
	else cd $(INSTALL_BASE) && git clone https://github.com/densho/ddr-cmdln.git; \
	fi

	cd $(INSTALL_BASE)/ddr-cmdln/ddr
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALL_BASE)/ddr-cmdln/ddr && python setup.py install
	source $(VIRTUALENV)/bin/activate; \
	pip install -U --download-cache=$(PIP_CACHE_DIR) -r $(INSTALL_BASE)/ddr-cmdln/ddr/requirements/production.txt

update-ddr-cmdln: install-virtualenv install-setuptools
	@echo ""
	@echo "ddr-cmdln --------------------------------------------------------------"
	cd $(INSTALL_BASE)/ddr-cmdln && git fetch && git pull
	cd $(INSTALL_BASE)/ddr-cmdln/ddr
	source $(VIRTUALENV)/bin/activate; \
	python setup.py install
	source $(VIRTUALENV)/bin/activate; \
	pip install -U --download-cache=$(PIP_CACHE_DIR) -r $(INSTALL_BASE)/ddr-cmdln/ddr/requirements/production.txt

uninstall-ddr-cmdln: install-virtualenv
	cd $(INSTALL_BASE)/ddr-cmdln/ddr
	source $(VIRTUALENV)/bin/activate; \
	-pip uninstall -r $(INSTALL_BASE)/ddr-cmdln/ddr/requirements/production.txt
	-rm /usr/local/bin/ddrindex
	-rm /usr/local/bin/ddrdensho255fix
	-rm /usr/local/bin/ddrmassupdate
	-rm /usr/local/bin/ddrfilter
	-rm /usr/local/bin/ddrpubcopy
	-rm /usr/local/bin/ddr
	-rm -Rf /usr/local/lib/python2.7/dist-packages/DDR
	-rm -Rf /usr/local/lib/python2.7/dist-packages/ddr-*

clean-ddr-cmdln:
	-rm -Rf $(INSTALL_BASE)/ddr-cmdln/ddr/build

# ddr-local is only used because it contains ddr.cfg
install-ddr-local: install-virtualenv
	@echo ""
	@echo "ddr-local --------------------------------------------------------------"
#	apt-get --assume-yes install imagemagick libexempi3 libssl-dev python-dev libxml2 libxml2-dev libxslt1-dev supervisor
	if test -d $(INSTALL_BASE)/ddr-local; \
	then cd $(INSTALL_BASE)/ddr-local && git pull; \
	else cd $(INSTALL_BASE) && git clone https://github.com/densho/ddr-local.git; \
	fi
#	source $(VIRTUALENV)/bin/activate; \
#	pip install -U --download-cache=$(PIP_CACHE_DIR) -r $(INSTALL_BASE)/ddr-local/ddrlocal/requirements/production.txt
# logs dir
	-mkdir /var/log/ddr
	chown -R ddr.root /var/log/ddr
	chmod -R 755 /var/log/ddr
## sqlite db dir
#	-mkdir /var/lib/ddr
#	chown -R ddr.root /var/lib/ddr
#	chmod -R 755 /var/lib/ddr
# media dir
	-mkdir -p $(MEDIA_ROOT)
	chown -R ddr.root $(MEDIA_ROOT)
	chmod -R 755 $(MEDIA_ROOT)

update-ddr-local:
	@echo ""
	@echo "ddr-local --------------------------------------------------------------"
	git fetch && git pull
#	source $(VIRTUALENV)/bin/activate; \
#	pip install -U --download-cache=$(PIP_CACHE_DIR) -r $(INSTALL_BASE)/ddr-local/ddrlocal/requirements/production.txt

uninstall-ddr-local:
	cd $(INSTALL_BASE)/ddr-local/ddrlocal
#	source $(VIRTUALENV)/bin/activate; \
#	-pip uninstall -r $(INSTALL_BASE)/ddr-local/ddrlocal/requirements/production.txt
	-rm /usr/local/lib/python2.7/dist-packages/ddrlocal-*
	-rm -Rf /usr/local/lib/python2.7/dist-packages/ddrlocal

clean-ddr-local:
	-rm -Rf $(INSTALL_BASE)/ddr-local/ddrlocal/src

install-ddr-public: install-virtualenv
	@echo ""
	@echo "ddr-public --------------------------------------------------------------"
	apt-get --assume-yes install imagemagick sqlite3 supervisor
	git pull
	source $(VIRTUALENV)/bin/activate; \
	pip install -U --download-cache=$(PIP_CACHE_DIR) -r $(INSTALLDIR)/ddrpublic/requirements/production.txt
# ddr repo
	-mkdir -p $(DDR_REPO_BASE)
	chown -R ddr.root $(DDR_REPO_BASE)
	chmod -R 755 $(DDR_REPO_BASE)
# logs dir
	-mkdir /var/log/ddr
	chown -R ddr.root /var/log/ddr
	chmod -R 755 /var/log/ddr
# sqlite db dir
	-mkdir /var/lib/ddr
	chown -R ddr.root /var/lib/ddr
	chmod -R 755 /var/lib/ddr

syncdb:
	source $(VIRTUALENV)/bin/activate; \
	cd $(INSTALLDIR)/ddrpublic && python manage.py syncdb --noinput
	chown -R ddr.root /var/lib/ddr
	chmod -R 750 /var/lib/ddr
	chown -R ddr.root /var/log/ddr
	chmod -R 755 /var/log/ddr

update-ddr-public:
	@echo ""
	@echo "ddr-public --------------------------------------------------------------"
	git fetch && git pull
	source $(VIRTUALENV)/bin/activate; \
	pip install -U --download-cache=$(PIP_CACHE_DIR) -r $(INSTALLDIR)/ddrpublic/requirements/production.txt

uninstall-ddr-public:
	cd $(INSTALLDIR)/ddrpublic
	source $(VIRTUALENV)/bin/activate; \
	-pip uninstall -r $(INSTALLDIR)/ddrpublic/requirements/production.txt
	-rm /usr/local/lib/python2.7/dist-packages/ddrpublic-*
	-rm -Rf /usr/local/lib/python2.7/dist-packages/ddrpublic

restart-ddrpublic:
	/etc/init.d/supervisor restart ddrpublic

clean-ddr-public:
	-rm -Rf $(INSTALLDIR)/ddrpublic/src

clean-pip:
	-rm -Rf $(PIP_CACHE_DIR)/*


branch:
	cd $(INSTALLDIR)/ddrpublic; python ./bin/git-checkout-branch.py $(BRANCH)


install-static: get-ddrpublic-assets install-modernizr install-bootstrap install-jquery

clean-static: clean-modernizr clean-bootstrap clean-jquery

get-ddrpublic-assets:
	@echo ""
	@echo "get assets --------------------------------------------------------------"
	-mkdir $(MEDIA_BASE)
	wget -nc -P /tmp http://$(PACKAGE_SERVER)/$(ASSETS)
	tar xzvf /tmp/ddr-public-assets.tar.gz -C $(MEDIA_BASE)/

install-modernizr:
	@echo ""
	@echo "Modernizr --------------------------------------------------------------"
	-rm $(STATIC_ROOT)/js/$(MODERNIZR)*
	wget -nc -P $(STATIC_ROOT)/js http://$(PACKAGE_SERVER)/$(MODERNIZR)

clean-modernizr:
	-rm $(STATIC_ROOT)/js/$(MODERNIZR)*

install-bootstrap:
	@echo ""
	@echo "Bootstrap --------------------------------------------------------------"
	wget -nc -P $(STATIC_ROOT) http://$(PACKAGE_SERVER)/$(BOOTSTRAP)
	7z x -y -o$(STATIC_ROOT) $(STATIC_ROOT)/$(BOOTSTRAP)

clean-bootstrap:
	-rm -Rf $(STATIC_ROOT)/$(BOOTSTRAP)

install-jquery:
	@echo ""
	@echo "jQuery -----------------------------------------------------------------"
	wget -nc -P $(STATIC_ROOT)/js http://$(PACKAGE_SERVER)/$(JQUERY)
	-ln -s $(STATIC_ROOT)/js/$(JQUERY) $(STATIC_ROOT)/js/jquery.js

clean-jquery:
	-rm -Rf $(STATIC_ROOT)/js/$(JQUERY)
	-rm $(STATIC_ROOT)/js/jquery.js


install-configs:
	@echo ""
	@echo "configuring ddr-public -------------------------------------------------"
# base settings file (from ddr-local)
# /etc/ddr/ddr.cfg must be readable by all
# /etc/ddr/local.cfg must be readable by ddr but contains sensitive info
	-mkdir /etc/ddr
	cp $(INSTALL_BASE)/ddr-local/debian/conf/ddr.cfg /etc/ddr/
	touch /etc/ddr/local.cfg
	python -c 'import random; print "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)])' > /etc/ddr/ddrpublic-secret-key.txt
	chown root.root /etc/ddr/ddr.cfg
	chown root.ddr /etc/ddr/local.cfg
	chown ddr.ddr /etc/ddr/ddrpublic-secret-key.txt
	chmod 644 /etc/ddr/ddr.cfg
	chmod 640 /etc/ddr/local.cfg
	chmod 640 /etc/ddr/ddrpublic-secret-key.txt
# web app settings
	cp $(INSTALLDIR)/debian/conf/settings.py $(INSTALLDIR)/ddrpublic/ddrpublic/
	chown root.root $(INSTALLDIR)/ddrpublic/ddrpublic/settings.py
	chmod 644 $(INSTALLDIR)/ddrpublic/ddrpublic/settings.py
# nginx settings
	cp $(INSTALLDIR)/debian/conf/ddrpublic.conf /etc/nginx/sites-available
	chown root.root /etc/nginx/sites-available/ddrpublic.conf
	chmod 644 /etc/nginx/sites-available/ddrpublic.conf
	-ln -s /etc/nginx/sites-available/ddrpublic.conf /etc/nginx/sites-enabled/ddrpublic.conf
	-rm /etc/nginx/sites-enabled/default
# supervisord
	cp $(INSTALLDIR)/debian/conf/supervisord.conf /etc/supervisor/
	cp $(INSTALLDIR)/debian/conf/gunicorn_ddrpublic.conf /etc/supervisor/conf.d/
	chown root.root /etc/supervisor/conf.d/gunicorn_ddrpublic.conf
	chmod 644 /etc/supervisor/conf.d/gunicorn_ddrpublic.conf

uninstall-configs:
	-rm /etc/nginx/sites-available/ddrpublic.conf
	-rm /etc/nginx/sites-enabled/ddrpublic.conf
	-rm /etc/supervisor/conf.d/gunicorn_ddrpublic.conf
	-rm $(INSTALL_BASE)/ddr-local/ddrpublic/ddrpublic/settings.py
	-rm /etc/ddr/ddrpublic-secret-key.txt
	-rm /etc/ddr/ddr.cfg


reload: reload-nginx reload-supervisor

reload-nginx:
	/etc/init.d/nginx reload

reload-supervisor:
	supervisorctl reload


restart: restart-elasticsearch restart-redis restart-nginx restart-supervisor

restart-elasticsearch:
	/etc/init.d/elasticsearch restart

restart-redis:
	/etc/init.d/redis-server restart

restart-nginx:
	/etc/init.d/nginx restart

restart-supervisor:
	/etc/init.d/supervisor restart


status:
	/etc/init.d/redis-server status
	/etc/init.d/elasticsearch status
	/etc/init.d/nginx status
	supervisorctl status

git-status:
	@echo "------------------------------------------------------------------------"
	cd $(INSTALL_BASE)/ddr-cmdln && git status
	@echo "------------------------------------------------------------------------"
	cd $(INSTALL_BASE)/ddr-local && git status
	@echo "------------------------------------------------------------------------"
	cd $(INSTALLDIR) && git status


install-ddr-manual:
	@echo ""
	@echo "ddr-manual --------------------------------------------------------------"
	pip install -U --download-cache=$(PIP_CACHE_DIR) sphinx
	if test -d $(INSTALL_BASE)/ddr-manual; \
	then cd $(INSTALL_BASE)/ddr-manual && git pull; \
	else cd $(INSTALL_BASE) && git clone https://github.com/densho/ddr-manual.git; \
	fi
	cd $(INSTALL_BASE)/ddr-manual && make html

update-ddr-manual:
	@echo ""
	@echo "ddr-manual --------------------------------------------------------------"
	cd $(INSTALL_BASE)/ddr-manual && git fetch && git pull
	cd $(INSTALL_BASE)/ddr-manual && make html

uninstall-ddr-manual:
	-pip uninstall sphinx

clean-ddr-manual:
	-rm -Rf $(INSTALL_BASE)/ddr-manual/build
