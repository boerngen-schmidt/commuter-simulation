#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

cd $BASE

function installPython3Debian {
	infoMsg "Creating Python 3 Virtual Environment"
	python3 -m venv --without-pip --copies python3-venv
	
	infoMsg "Installing setuptools for virtual environment"
	wget -P $TMPDIR https://pypi.python.org/packages/source/s/setuptools/setuptools-5.7.tar.gz#md5=81f980854a239d60d074d6ba052e21ed > /dev/null
	tar xfz $TMPDIR/setuptools-5.7.tar.gz -C $TMPDIR > /dev/null
	
	infoMsg "Activating Python 3 Virtual Environment"
	source $BASE/python3-venv/bin/activate
	
	infoMsg "Installing Setuptools"
	python3 $TMPDIR/setuptools-5.7/ez_setup.py > /dev/null
	
	infoMsg "Installing Pip"
	easy_install pip > /dev/null
}

function installPython3Gentoo {
	infoMsg "Creating Python 3 Virtual Environment"
	virtualenv --clear python3-venv
	
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
pip install psycopg2 simpy

infoMsg "Exiting Python 3 Virtual Environment"
deactivate