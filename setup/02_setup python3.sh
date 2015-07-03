#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

cd $BASE

function installPython3Debian {
	infoMsg "Creating Python 3 Virtual Environment"
	python3 -m venv --without-pip --copies python3-venv
	
	infoMsg "Activating Python 3 Virtual Environment"
	source $BASE/python3-venv/bin/activate
	
	infoMsg "Installing Setuptools"
	wget https://bootstrap.pypa.io/ez_setup.py -O - | python > /dev/null

	infoMsg "Installing Pip"
	easy_install pip > /dev/null
}

function installPython3Gentoo {
	infoMsg "Creating Python 3 Virtual Environment"
	#virtualenv --clear python3-venv --python=/usr/bin/python3.4
	python3.4 -m venv --clear python3-venv
	
	infoMsg "Activating Python 3 Virtual Environment"
	source $BASE/python3-venv/bin/activate
}

infoMsg "Installing Python 3"
if [ $(currentDistribution) == $DIST_DEBIAN ]; then
	installPython3Debian
elif [ $(currentDistribution) == $DIST_GENTOO ]; then
	installPython3Gentoo
fi

infoMsg "Installing Packages"
pip install cython psycopg2 PyYaml numpy Shapely pyzmq
# pip install --global-option=build_ext --global-option="-I/usr/include/gdal" gdal

infoMsg "Exiting Python 3 Virtual Environment"
deactivate