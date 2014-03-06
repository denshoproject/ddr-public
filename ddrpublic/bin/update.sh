# update.sh - Pulls down new code, copies configs, restarts
#
# NOTE: This script must be run as root!
# 
# WARNING: This script makes assumptions!
# - That ddr-lint is installed in /usr/local/src.
# - That ddr-cmdln is installed in /usr/local/src.
# - That ddr-local is installed in /usr/local/src.
# - That ddr-public is installed in /usr/local/src.
# If these is not the case, expect breakage!
#
# NOTE: Does not flush caches.


echo "<([ elasticsearch ])>-------------------------------------------------------"

echo "/etc/elasticsearch/elasticsearch.yml"
cp /usr/local/src/ddr-public/debian/conf/elasticsearch.yml /etc/elasticsearch/
chown root.root /etc/elasticsearch/elasticsearch.yml
chmod 644 /etc/elasticsearch/elasticsearch.yml

echo "/etc/init.d/elasticsearch restart"
/etc/init.d/elasticsearch restart


echo "<([ ddr-lint ])>-------------------------------------------------------"
cd /usr/local/src/ddr-lint

echo "git fetch"
git fetch

echo "git pull"
git pull

echo "python setup.py install"
cd /usr/local/src/ddr-lint/ddrlint
python setup.py install


echo "<([ ddr-cmdln ])>-------------------------------------------------------"
cd /usr/local/src/ddr-cmdln

echo "git fetch"
git fetch

echo "git pull"
git pull

echo "python setup.py install"
cd /usr/local/src/ddr-cmdln/ddr
python setup.py install


echo "<([ ddr-local ])>-------------------------------------------------------"
cd /usr/local/src/ddr-local

echo "git fetch"
git fetch

echo "git pull"
git pull

echo "/etc/ddr/ddr.cfg"
cp /usr/local/src/ddr-local/debian/conf/ddr.cfg /etc/ddr/


echo "<([ ddr-public ])>------------------------------------------------------"
cd /usr/local/src/ddr-public

echo "git fetch"
git fetch

echo "git pull"
git pull

echo "./ddrpublic/ddrpublic/settings.py"
cp /usr/local/src/ddr-public/debian/conf/settings.py /usr/local/src/ddr-public/ddrpublic/ddrpublic

echo "/etc/nginx/sites-available/ddrpublic.conf"
cp /usr/local/src/ddr-public/debian/conf/ddrpublic.conf /etc/nginx/sites-available
rm /etc/nginx/sites-enabled/ddrpublic.conf
ln -s /etc/nginx/sites-available/ddrpublic.conf /etc/nginx/sites-enabled
rm /etc/nginx/sites-enabled/default
/etc/init.d/nginx restart

echo "/etc/supervisor/supervisord.conf"
cp /usr/local/src/ddr-public/debian/conf/supervisord.conf /etc/supervisor/

echo "/etc/supervisor/conf.d/gunicorn_ddrpublic.conf"
cp /usr/local/src/ddr-public/debian/conf/gunicorn_ddrpublic.conf /etc/supervisor/conf.d/


echo "<([ restarting services ])>---------------------------------------------"

echo "supervisord restart"
/etc/init.d/supervisor restart

echo "supervisorctl status"
supervisorctl status

echo "/etc/init.d/nginx restart"
/etc/init.d/nginx restart


echo "<([ DONE ])>"
