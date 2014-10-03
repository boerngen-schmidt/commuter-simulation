#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

cd $BASE

infoMsg "Creating Python 3 Virtual Environment"
python3 -m venv --without-pip --copies python3-venv
wget -P $TMPDIR https://pypi.python.org/packages/source/s/setuptools/setuptools-5.7.tar.gz#md5=81f980854a239d60d074d6ba052e21ed
tar xvfz $TMPDIR/setuptools-5.7.tar.gz

infoMsg "Activating Python 3 Virtual Environment"
source $BASE/python3-venv/bin/activate

infoMsg "Installing Setuptools"
python3 $TMPDIR/setuptools-5.7/ez_setup.py 

infoMsg "Installing Pip"
easy_install pip

infoMsg "Installing Packages"
pip install psycopg2 simpy

infoMsg "Exiting Python 3 Virtual Environment"
deactivate