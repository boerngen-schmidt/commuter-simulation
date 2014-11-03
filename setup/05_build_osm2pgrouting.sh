#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

function installDebian {
	sudo apt-get -y install git cmake build-essential libexpat1-dev libboost-dev libpq-dev
}

function installGentoo {
	emerge osm2pgrouting
}

function buildOsm2pgrouting {
	infoMsg "Installing needed packages"
	if currentDistribution -eq $DIST_DEBIAN; then
		installDebian
		infoMsg "Cloning git repository"
		cd $TMPDIR
		rm -rf $TMPDIR/osm2pgrouting
		git clone https://github.com/pgRouting/osm2pgrouting.git
		
		infoMsg "Compiling osm2pgrouting"
		cd osm2pgrouting
		cmake -H. -Bbuild
		cd build
		make
	elif currentDistribution -eq $DIST_GENTOO; then
		installGentoo
	fi
}

$(ynQuestion "Do you want to build osm2pgrouting from sources?")
if [ $? -eq 1]; then
    buildOsm2pgrouting
fi

cd $BASE