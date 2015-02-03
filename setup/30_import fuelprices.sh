#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

infoMsg "Droping mySQL database for fuelprices"
#read -s -p "Please enter password for mysql user 'root': " MYSQL_PASSWD
mysqladmin --login-path=local drop spritsim
mysqladmin --login-path=local create spritsim

infoMsg "Importing fuelprices into mySQL database"
mysql --login-path=local -D spritsim < $BASE/data/fuel/stations.sql
#mysql --login-path=local -D spritsim < $BASE/data/fuel/priceinfo.sql
mysql --login-path=local -D spritsim < $BASE/data/fuel/2014_06.sql
mysql --login-path=local -D spritsim < $BASE/data/fuel/2014_07.sql
mysql --login-path=local -D spritsim < $BASE/data/fuel/2014_08_01.sql
mysql --login-path=local -D spritsim < $BASE/data/fuel/2014_08_02.sql
mysql --login-path=local -D spritsim < $BASE/data/fuel/2014_09.sql
mysql --login-path=local -D spritsim < $BASE/data/fuel/2014_10.sql


infoMsg "Migrating data to PostgreSQL"
source $BASE/python2-venv/bin/activate
py-mysql2pgsql -f $BASE/config/py-mysql2pgsql.yml -v
deactivate

infoMsg "Running post-import scripts"
psql -q -f $BASE/config/postgresql/post-import_stations.sql -d $DATABASE -U $USER
psql -q -f $BASE/config/postgresql/post-import_priceinfo.sql -d $DATABASE -U $USER
