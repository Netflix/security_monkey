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
fpm -s dir -t deb -n securitymonkey -v 0.41 --iteration 13 -d "python-psycopg2,libpq-dev,supervisor,libffi-dev,apache2" --after-install packaging/long_post_install_new.sh . 
