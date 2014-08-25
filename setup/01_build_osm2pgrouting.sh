#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

apt-get install git cmake libexpat1-dev libboost-dev libpq-dev

cd $BASE/src/
git clone https://github.com/pgRouting/osm2pgrouting.git
cd osm2pgrouting
cmake -H. -Bbuild
cd build
make
make install
