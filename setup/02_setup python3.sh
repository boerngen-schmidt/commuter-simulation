#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

cd $BASE

infoMsg "Creating Python 3 Virtual Environment"
python3 -m venv --without-pip --copies python3-venv
wget -P $TMPDIR https://pypi.python.org/packages/source/s/setuptools/setuptools-5.7.tar.gz#md5=81f980854a239d60d074d6ba052e21ed > /dev/null
tar xfz $TMPDIR/setuptools-5.7.tar.gz -C $TMPDIR > /dev/null

infoMsg "Activating Python 3 Virtual Environment"
source $BASE/python3-venv/bin/activate

infoMsg "Installing Setuptools"
python3 $TMPDIR/setuptools-5.7/ez_setup.py > /dev/null

infoMsg "Installing Pip"
easy_install pip > /dev/null

infoMsg "Installing Packages"
pip install psycopg2 simpy > /dev/null

infoMsg "Exiting Python 3 Virtual Environment"
deactivate