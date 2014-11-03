#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

echo; echo;
echo -e "\e[92mStoping PostgreSQL Server \e[39m..."
sudo PostgresService stop

postgres_conf=$(find /etc/ -name postgresql.conf)
postgres_dir=$(dirname $postgres_conf)
infoMsg "Copying configuration files"
if ! grep -q postgresql.conf.include $postgres_conf; then
	echo -e "\n\ninclude = 'postgresql.conf.include'" | sudo tee --append $postgres_conf >/dev/null
fi
sudo cp $BASE/config/postgresql/postgresql.conf.include $postgres_dir
sudo chown postgres:postgres $postgres_dir/postgresql.conf.include

infoMsg "Starting PostgreSQL Server"
sudo PostgresService start

echo; echo;
infoMsg "Enter Password for user \"postgres\""
sudo su -c "psql -c \"\password\"" postgres
echo;
infoMsg "Creating user \"$USER\""
sudo su -c "createuser --superuser $USER" postgres
infoMsg "Please enter password for \"$USER\""
sudo su -c "psql -c \"\password $USER\"" postgres
	
echo; echo;
infoMsg "Checking if database \"$DATABASE\" exists"
# Check if database exists. if so drop it and create it again
DBEXISTS=`psql -At -c "SELECT count(*) FROM pg_database where datname='$DATABASE'" -d postgres -U $USER`
if [ $DBEXISTS == 1 ]; then
	yn = ynQuestion "Do you want to drop the database?"
	if [ $yn ]; then
			if [ ynQuestion "Do you REALLY want to drop the database?" ]; then
				infoMsg "Dropping database \"$DATABASE\""
				dropdb -U $USER --if-exists $DATABASE
				infoMsg "Creating Database for routing"
				createdb -U $USER -E UTF8 -O $USER $DATABASE
			fi
	else
		infoMsg "Skipped dropping database"
	fi
else
	infoMsg "Creating Database for routing"
	createdb -U $USER -E UTF8 -O $USER $DATABASE
fi