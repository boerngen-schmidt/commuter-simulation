python3 -m venv --without-pip --copies python3-venv
wget https://pypi.python.org/packages/source/s/setuptools/setuptools-5.7.tar.gz#md5=81f980854a239d60d074d6ba052e21ed
tar xvfz $TMP_DIR/setuptools-5.7.tar.gz
source $BASE/python3-venv/bin/activate
python3 tmp/setuptools-5.7/ez_setup.py 
easy_install pip
pip install psycopg2 simpy pytest