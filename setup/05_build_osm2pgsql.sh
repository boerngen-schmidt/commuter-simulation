#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

function buildOSM2PGSQL {
	infoMsg "Installing needed packages"
	if [ $(currentDistribution) == $DIST_DEBIAN ]; then
		sudo apt-get install -y libboost-all-dev git libxml2-dev libgeos-dev libgeos++-dev libpq-dev libbz2-dev libproj-dev protobuf-c-compiler libprotobuf-c0-dev autoconf automake libtool make g++
	elif [ $(currentDistribution) == $DIST_GENTOO ]; then
		doemerge "boost git dev-cpp/libxmlpp geos libpqxx bzip2 proj protobuf-c"
	fi
	
	infoMsg "Cloning git repository"
	git -C $TMPDIR clone git://github.com/MapQuest/osm2pgsql.git		
				
	infoMsg "Compiling osm2pgsql C++"
	cd $TMPDIR/osm2pgsql
	./autogen.sh
	./configure && make -j 8

	infoMsg "Installing osm2pgsql locally"
	cp osm2pgsql $BASE/bin												
}

if [ $(ynQuestion "Do you want to build osm2pgsql from sources?") ]; then
	# remove old stuff
	rm -rf $TMPDIR/osm2pgsql
	buildOSM2PGSQL
	 
fi

cd $BASE