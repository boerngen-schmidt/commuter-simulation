#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

function buildOSM2PGSQL {
	infoMsg "Installing needed packages"
	sudo apt-get install -y git libxml2-dev libgeos-dev libgeos++-dev libpq-dev libbz2-dev libproj-dev protobuf-c-compiler libprotobuf-c0-dev autoconf automake libtool make g++
	
	infoMsg "Cloning git repository"
	git -C $TMPDIR clone git://github.com/openstreetmap/osm2pgsql.git
	
	infoMsg "Compiling osm2pgsql"
	cd $TMPDIR/osm2pgsql
	./autogen.sh
	./configure && make
	
	infoMsg "Installing osm2pgsql locally"
	cp $TMPDIR/osm2pgsql/osm2pgsql $BASE/bin
}

function buildOSM2PGSQLCPP {
	infoMsg "Installing needed packages"
	if currentDistribution -eq $DIST_DEBIAN; then
		sudo apt-get install -y libboost-all-dev git libxml2-dev libgeos-dev libgeos++-dev libpq-dev libbz2-dev libproj-dev protobuf-c-compiler libprotobuf-c0-dev autoconf automake libtool make g++
	elif currentDistribution -eq $DIST_GENTOO; then
		emerge boost git libxml geos libpqxx bzip2 proj protobuf-c
	fi
	
	infoMsg "Cloning git repository"
	git -C $TMPDIR clone git://github.com/MapQuest/osm2pgsql.git		
				
	infoMsg "Compiling osm2pgsql C++"
	cd $TMPDIR/osm2pgsql
	./autogen.sh
	./configure && make

	infoMsg "Installing osm2pgsql locally"
	cp osm2pgsql $BASE/bin												
}

$(ynQuestion "Do you want to build osm2pgsql from sources?")
if [ $? -eq 1 ]; then
	# remove old stuff
	rm -rf $TMPDIR/osm2pgsql
	select type in "C Version" "C++ Version"; do
	    case $REPLY in
	        1) buildOSM2PGSQL;;
	        2) buildOSM2PGSQLCPP;;
	        *) $REPLY=;;
	    esac
	done

cd $BASE
