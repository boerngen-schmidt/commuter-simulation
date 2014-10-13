#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

function buildOsm2pgrouting {
	infoMsg "Installing needed packages"
	sudo apt-get -y install git cmake build-essential libexpat1-dev libboost-dev libpq-dev
	
	infoMsg "Cloning git repository"
	cd $TMPDIR
	rm -rf $TMPDIR/osm2pgrouting
	git clone https://github.com/pgRouting/osm2pgrouting.git
	
	infoMsg "Compiling osm2pgrouting"
	cd osm2pgrouting
	cmake -H. -Bbuild
	cd build
	make
}

warnMsg "Do you want to build osm2pgrouting from sources?"
select yn in "Yes" "No"; do
    case "$yn" in
        Yes) buildOsm2pgrouting
        	break
        	;;
        No) exit;;
    esac
done

cd $BASE