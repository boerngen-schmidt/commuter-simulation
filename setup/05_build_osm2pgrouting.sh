#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

function installDebian {
	sudo apt-get -y install git cmake build-essential libexpat1-dev libboost-dev libpq-dev
}

function installGentoo {
	#emerge osm2pgrouting
	doemerge "boost git dev-cpp/libxmlpp geos libpqxx"
}

function buildOsm2pgrouting {
	infoMsg "Installing needed packages"
	if [ $(currentDistribution) == $DIST_DEBIAN ]; then
		installDebian
	elif [ $(currentDistribution) == $DIST_GENTOO ]; then
		installGentoo
	fi
	
	infoMsg "Cloning git repository"
	cd $TMPDIR
	rm -rf $TMPDIR/osm2pgrouting
	git clone https://github.com/pgRouting/osm2pgrouting.git
	
	infoMsg "Compiling osm2pgrouting"
	cd osm2pgrouting
	cmake -H. -Bbuild
	cd build
		make -j8
}

if [ $(ynQuestion "Do you want to build osm2pgrouting from sources?") ]; then
    buildOsm2pgrouting
fi

cd $BASE