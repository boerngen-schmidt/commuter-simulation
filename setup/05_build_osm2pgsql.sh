#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

function buildOSM2PGSQL {
	infoMsg "Installing needed packages"
	sudo apt-get install -y git libxml2-dev libgeos-dev libgeos++-dev libpq-dev libbz2-dev libproj-dev protobuf-c-compiler libprotobuf-c0-dev autoconf automake libtool make g++ libbz2-dev
	
	# remove old stuff
	rm -rf $TMPDIR/osm2pgsql
	
	infoMsg "Cloning git repository"
	git -C $TMPDIR clone git://github.com/openstreetmap/osm2pgsql.git
	
	infoMsg "Compiling osm2pgsql"
	cd $TMPDIR/osm2pgsql
	./autogen.sh
	./configure && make
	
	infoMsg "Installing osm2pgsql"
	cp $TMPDIR/osm2pgsql/osm2pgsql $BASE/bin
}

warnMsg "Do you want to build osm2pgsql from sources?"
select yn in "Yes" "No"; do
    case "$yn" in
        Yes) buildOSM2PGSQL
        	break
        	;;
        No) exit;;
    esac
done

cd $BASE