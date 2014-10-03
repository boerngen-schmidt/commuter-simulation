#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

read -p "Please enter password for mysql user 'root': " MYSQL_PASSWD

mysql -uroot -p$MYSQL_PASSWD < "CREATE DATABASE `spritsim` /*!40100 DEFAULT CHARACTER SET utf8 */;"
mysql -uroot -p$MYSQL_PASSWD -D spritsim < $TMP/fuel/stations.sql
mysql -uroot -p$MYSQL_PASSWD -D spritsim < $TMP/fuel/priceinfo.sql

py-mysql2pgsql -f $BASE/config/py-mysql2pgsql.yml
