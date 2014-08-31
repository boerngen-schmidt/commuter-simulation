#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

echo; echo;
echo -e "\e[92mStoping PostgreSQL Server \e[39m..."
sudo /etc/init.d/postgresql stop

echo -e "\e[92mCopying configuration files \e[39m..."
if ! grep -q postgresql.conf.include /etc/postgresql/9.3/main/postgresql.conf; then
	echo -e "\n\ninclude = 'postgresql.conf.include'" | sudo tee --append /etc/postgresql/9.3/main/postgresql.conf >/dev/null
fi
sudo cp $BASE/config/postgresql/postgresql.conf.include /etc/postgresql/9.3/main/
sudo chown postgres:postgres /etc/postgresql/9.3/main/postgresql.conf.include

echo -e "\e[92mStarting PostgreSQL Server \e[39m..."
sudo /etc/init.d/postgresql start

echo; echo;
echo -e "\e[92mEnter Password for user \"postgres\" :\e[39m"
sudo -u postgres psql postgres -c "\password"
echo;
echo -e "\e[92mCreating user \"$USER\" \e[39m..."
sudo -u postgres createuser --superuser $USER
echo -e "\e[92mPlease enter password for \"$USER\"\e[39m"
sudo -u postgres psql -c "\password $USER"
	
echo; echo;
echo -e "\e[92mChecking if database \"$DATABASE\" exists \e[39m..."
# Check if database exists. if so drop it and create it again
DBEXISTS=`psql -At -c "SELECT count(*) FROM pg_database where datname='$DATABASE'" -d postgres -U $USER`
if [ $DBEXISTS == 1 ]; then
	echo
	echo -e "\e[31mDo you want to drop the database? \e[39m"
	read -p "[y/N]: " yn
	case $yn in
		[Yy]* ) 
			read -p "Do you REALLY want to drop the database? Type YES to confirm: " reallyYes
			if [[ $reallyYes == "YES" ]]; then 
				echo -e "\e[92mDropping database \"$DATABASE\" \e[39m..."
				dropdb -U $USER --if-exists $DATABASE
				echo -e "\e[31mCreating Database for routing \e[39m..."
				createdb -U $USER -E UTF8 -O $USER $DATABASE
			fi
			;;
		* ) echo "Skipped dropping database"
			;;
	esac
else
	echo -e "\e[31mCreating Database for routing \e[39m..."
	createdb -U $USER -E UTF8 -O $USER $DATABASE
fi
