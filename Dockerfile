# Copyright 2018 Netflix, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM ubuntu:latest
MAINTAINER Netflix Open Source Development <talent@netflix.com>

ENV SECURITY_MONKEY_VERSION=v1.0 \
    SECURITY_MONKEY_SETTINGS=/usr/local/src/security_monkey/env-config/config-docker.py

SHELL ["/bin/bash", "-c"]
RUN apt-get update && apt-get upgrade -y && apt-get install --no-install-recommends -y build-essential python-pip python-dev && apt-get clean -y

RUN apt-get install --no-install-recommends -y wget postgresql postgresql-contrib libpq-dev nginx supervisor git libffi-dev && apt-get clean -y

RUN pip install setuptools --upgrade && \
    pip install pip --upgrade && \
    hash -d pip && \
    pip install "urllib3[secure]" --upgrade && \
    pip install google-compute-engine && \
    pip install cloudaux\[gcp\] && \
    pip install cloudaux\[openstack\]

RUN pip install 'six>=1.11.0' \
        'cloudaux==1.4.13' \
        'celery==4.2.0rc2' \
        'celery[redis]==4.2.0rc2' \
        'redis==2.10.6' \
        'Flask>=0.12.2' \
        'Flask-Mail==0.9.1' \
        'Flask-Migrate==2.1.1' \
        'Flask-Principal==0.4.0' \
        'Flask-RESTful==0.3.6' \
        'Flask-SQLAlchemy==1.0' \
        'Flask-Script==0.6.3' \
        'Flask-Security>=3.0.0' \
        'Flask-WTF>=0.14.2' \
        'Jinja2>=2.10' \
        'SQLAlchemy==1.2.5' \
        'boto>=2.48.0' \
        'ipaddr==2.2.0' \
        'itsdangerous==0.24' \
        'psycopg2==2.7.4' \
        'bcrypt==3.1.4' \
        'gunicorn==19.7.1' \
        'cryptography>=1.8.1' \
        'dpath==1.4.2' \
        'pyyaml>=3.12' \
        'jira==1.0.14' \
        'policyuniverse>=1.1.0.1' \
        'joblib>=0.9.4' \
        'pyjwt>=1.01' \
        'netaddr' \
        'swag-client>=0.3.7' \
        'idna==2.6' \
        'marshmallow==2.15.0' \
        'flask-marshmallow==0.8.0'
    
ADD . /usr/local/src/security_monkey

RUN cd /usr/local/src/security_monkey && \
    chown -R www-data /usr/local/src/security_monkey && \
    pip install . && \
    /bin/mkdir -p /var/log/security_monkey/ && \
    chmod +x /usr/local/src/security_monkey/docker/*.sh && \
    /usr/bin/touch /var/log/security_monkey/securitymonkey.log && \
    chmod -R guo+r /usr/local/src/security_monkey && \
    find /usr/local/src/security_monkey -type d -exec chmod 755 {} \;

WORKDIR /usr/local/src/security_monkey
EXPOSE 5000
