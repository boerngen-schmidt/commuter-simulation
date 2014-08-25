#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

echo -e "\e[92mInstalling nessesary Packages \e[39m..."
sudo add-apt-repository -y ppa:georepublic/pgrouting >/dev/null 2>&1
sudo apt-get -q update >/dev/null

PACKAGES="postgresql postgresql-contrib postgis postgresql-9.3-pgrouting osm2pgrouting osm2pgsql pgadmin3"
sudo apt-get -q -y install $PACKAGES

echo; echo;
echo -e "\e[92mStarting PostgreSQL Server \e[39m..."
sudo /etc/init.d/postgresql start

echo; echo;
echo -e "\e[92mEnter Password for user \"postgres\" :"
sudo -u postgres psql postgres -c "\password"
echo;
echo -e "\e[92mCreating user \"$USER\" \e[39m..."
sudo -u postgres createuser --superuser $USER
echo -e "\e[92mPlease enter password for \"$USER\""
sudo -u postgres psql -c "\password $USER"

read -p "Download latest OSM Germany Map? [y/N]: " yn
case $yn in
	[Yy]* ) wget http://download.geofabrik.de/europe/germany-latest.osm.pbf -P $BASE/src/ -N;;
	* ) echo "  Skipped downloading OSM Data";;
esac

echo; echo;
echo -e "\e[92mDownloading OSM2PO  \e[39m..."
wget -P $BASE/src/ "http://osm2po.de/download.php?lnk=osm2po-4.8.8.zip" --referer http://osm2po.de --content-disposition -N
unzip $BASE/src/osm2po-4.8.8.zip -d $BASE/osm2po

echo; echo;
echo -e "\e[92mCopying osm2pgsql default.style \e[39m..."
echo "Please edit the style and rename it to \"default.style\""
mkdir -p $BASE/osm2pgsql
cp  /usr/share/osm2pgsql/default.style $BASE/lib/osm2pgsql/default.style-orginal
