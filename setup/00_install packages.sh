#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi


echo -e "\e[92mInstalling nessesary Packages \e[39m..."
sudo add-apt-repository -y ppa:georepublic/pgrouting >/dev/null 2>&1
sudo apt-get -q update >/dev/null

PACKAGES="postgresql postgresql-contrib postgis postgresql-9.3-pgrouting osm2pgrouting osm2pgsql pgadmin3"
sudo apt-get -q -y install $PACKAGES

read -p "Download latest OSM Germany Map? [y/N]: " yn
case $yn in
	[Yy]* ) 
		wget http://download.geofabrik.de/europe/germany-latest.osm.pbf -P $TMPDIR -N
		wget http://download.geofabrik.de/europe/germany-latest.osm.bz2 -P $TMPDIR -N
		;;
	* ) echo "  Skipped downloading OSM Data";;
esac

echo; echo;
echo -e "\e[92mDownloading OSM2PO  \e[39m..."
wget -P $TMPDIR "http://osm2po.de/download.php?lnk=osm2po-4.8.8.zip" --referer http://osm2po.de --content-disposition -N
unzip $TMPDIR/osm2po-4.8.8.zip -d $BASE/bin/osm2po

#echo; echo;
#echo -e "\e[92mCopying osm2pgsql default.style \e[39m..."
#echo "Please edit the style and rename it to \"default.style\""
#mkdir -p $BASE/osm2pgsql
#cp  /usr/share/osm2pgsql/default.style $BASE/config/osm2pgsql/default.style-orginal
