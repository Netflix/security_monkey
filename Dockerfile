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

ADD . /usr/local/src/security_monkey

SHELL ["/bin/bash", "-c"]
RUN apt-get update && \
    apt-get install -y wget build-essential python-pip python-dev python-psycopg2 postgresql postgresql-contrib libpq-dev nginx supervisor git libffi-dev gcc python-virtualenv -y && \
    cd /usr/local/src/security_monkey && \
    chown -R www-data /usr/local/src/security_monkey && \
    virtualenv venv && \
    source venv/bin/activate && \
    pip install setuptools --upgrade && \
    pip install pip --upgrade && \
    pip install "urllib3[secure]" --upgrade && \
    pip install google-compute-engine && \
    pip install cloudaux\[gcp\] && \
    pip install cloudaux\[openstack\] && \
    pip install . && \
    /bin/mkdir -p /var/log/security_monkey/ && \
    chmod +x /usr/local/src/security_monkey/docker/*.sh && \
    /usr/bin/touch /var/log/security_monkey/securitymonkey.log && \
    chmod -R guo+r /usr/local/src/security_monkey && \
    find /usr/local/src/security_monkey -type d -exec chmod 755 {} \;

WORKDIR /usr/local/src/security_monkey
EXPOSE 5000
