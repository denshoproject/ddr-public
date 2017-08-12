# After installing (FPM) .deb package, make logs directory
mkdir -p /var/log/ddr
chmod 755 /var/log/ddr
chown -R ddr.ddr /var/log/ddr
# Sqlite3 database dir
mkdir -p /var/lib/ddr
chmod 755 /var/lib/ddr
chown -R ddr.ddr /var/lib/ddr
