#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

infoMsg "Droping mySQL database for fuelprices"
read -s -p "Please enter password for mysql user 'root': " MYSQL_PASSWD
mysqladmin -uroot -p$MYSQL_PASSWD drop spritsim
mysqladmin -uroot -p$MYSQL_PASSWD create spritsim

infoMsg "Importing fuelprices into mySQL database"
mysql -uroot -p$MYSQL_PASSWD -D spritsim < $BASE/data/fuel/stations.sql
mysql -uroot -p$MYSQL_PASSWD -D spritsim < $BASE/data/fuel/priceinfo.sql

infoMsg "Migrating data to PostgreSQL"
source $BASE/python2-venv/bin/activate
py-mysql2pgsql -f $BASE/config/py-mysql2pgsql.yml -v
deactivate

infoMsg "Running post-import scripts"
psql -q -f $BASE/config/postgresql/post-import_stations.sql -d $DATABASE -U $USER
psql -q -f $BASE/config/postgresql/post-import_priceinfo.sql -d $DATABASE -U $USER
