#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

function buildOSM2PGSQL {
	sudo apt-get install -y git libxml2-dev libgeos-dev libgeos++-dev libpq-dev libbz2-dev libproj-dev protobuf-c-compiler libprotobuf-c0-dev autoconf automake libtool make g++ libbz2-dev
	
	# remove old stuff
	rm -rf $TMPDIR/osm2pgsql
	
	git -C $TMPDIR clone git://github.com/openstreetmap/osm2pgsql.git
	
	cd $TMPDIR/osm2pgsql
	./autogen.sh
	./configure && make
	cp $TMPDIR/osm2pgsql/osm2pgsql $BASE/bin
}

echo; echo;
echo "Do you want to build osm2pgsql from sources?"
select yn in "Yes" "No"; do
    case "$yn" in
        Yes) buildOSM2PGSQL
        	break
        	;;
        No) exit;;
    esac
done

cd $BASE