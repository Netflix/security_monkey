# setup the environment variable file with our credentials
cp `echo $security_monkey_secrets` env

# setup and activate the python virutal environment
virtualenv security_monkey
. security_monkey/bin/activate

cd security_monkey
# install all the python libraries that are dependencies
pip install -r ../requirements.txt

cd ..
# install the securitymonkey python package
python setup.py install

/usr/lib/dart/bin/pub get
/usr/lib/dart/bin/pub build

# build the deb using fpm
fpm -s dir -t deb -n security-monkey -v 0.41 --iteration 12 -d "python-psycopg2,postgresql,postgresql-contrib,libpq-dev,supervisor,libffi-dev,nginx" --after-install packaging/long_post_install_new.sh security_monkey
