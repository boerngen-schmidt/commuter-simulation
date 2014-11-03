#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

cd $BASE

if currentDistribution -eq $DIST_DEBIAN; then
	sudo apt-get -q -y install python-virtualenv python-pip libyaml-dev
elif currentDistribution -eq $DIST_GENTOO; then
	emerge dev-python/pip dev-python/virtualenv dev-libs/libyaml
fi
virtualenv -p /usr/bin/python2.7 --clear $BASE/pyt	hon2-venv/

infoMsg "Activating Python 2 Virtual Environment"
source $BASE/python2-venv/bin/activate

infoMsg "Installing Python 2 packages"
pip install py-mysql2pgsql

if [ ! -f $BASE/config/py-mysql2pgsql.yml ]; then
	infoMsg "Creating default py-mysql2pgsql config file"
	py-mysql2pgsql -f $BASE/config/py-mysql2pgsql.yml
	warnMsg "Please configure connection settings"
fi

infoMsg "Deactivating Python 2 Virtual Environment"
deactivate