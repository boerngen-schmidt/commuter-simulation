#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

function buildOsm2pgrouting {
	sudo apt-get -y install git cmake libexpat1-dev libboost-dev libpq-dev
	
	cd $TMPDIR
	git clone https://github.com/pgRouting/osm2pgrouting.git
	cd osm2pgrouting
	cmake -H. -Bbuild
	cd build
	make
	make install
}

echo; echo;
echo "Do you want to build osm2pgrouting from sources?"
select yn in "Yes" "No"; do
    case "$yn" in
        Yes) buildOsm2pgrouting
        	break
        	;;
        No) exit;;
    esac
done

cd $BASE