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

FROM ubuntu:xenial
MAINTAINER Netflix Open Source Development <talent@netflix.com>

ENV SECURITY_MONKEY_VERSION=v1.1.3 \
    SECURITY_MONKEY_SETTINGS=/usr/local/src/security_monkey/env-config/config-docker.py

SHELL ["/bin/bash", "-c"]
WORKDIR /usr/local/src/security_monkey
COPY requirements.txt /usr/local/src/security_monkey/

RUN echo "UTC" > /etc/timezone

RUN apt-get update && \
    apt-get upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y build-essential python-pip python-dev && \
    DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y wget postgresql postgresql-contrib libpq-dev libffi-dev libxml2-dev libxmlsec1-dev && \
    apt-get clean -y && \
    pip install setuptools --upgrade && \
    pip install pip --upgrade && \
    hash -d pip && \
    pip install "urllib3[secure]" --upgrade && \
    pip install google-compute-engine && \
    pip install cloudaux\[gcp\] && \
    pip install cloudaux\[openstack\] && \
    pip install python-saml && \
    pip install -r requirements.txt
    
COPY . /usr/local/src/security_monkey
RUN pip install ."[onelogin]" && \
    /bin/mkdir -p /var/log/security_monkey/ && \
    /usr/bin/touch /var/log/security_monkey/securitymonkey.log

EXPOSE 5000
