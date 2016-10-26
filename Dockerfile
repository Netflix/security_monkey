
# Copyright 2014 Netflix, Inc.
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

FROM ubuntu:14.04
MAINTAINER Netflix Open Source Development <talent@netflix.com>

RUN apt-get update &&\
  apt-get -y -q install python-software-properties software-properties-common postgresql-9.3 postgresql-client-9.3 postgresql-contrib-9.3 curl &&\
  apt-get install -y python-pip python-dev python-psycopg2 libpq-dev git sudo swig python-m2crypto &&\
  cd /usr/local/src &&\
  git clone -b v0.3.4 --branch master https://github.com/Netflix/security_monkey.git &&\
  cd security_monkey &&\
  python setup.py install &&\
  /bin/mkdir -p /var/log/security_monkey/

ADD api-start.sh /usr/local/src/security_monkey/scripts/api-start.sh
ADD config-deploy.py /usr/local/src/security_monkey/env-config/config-deploy.py

RUN chmod +x /usr/local/src/security_monkey/scripts/api-start.sh

EXPOSE 5000

ENTRYPOINT ["/usr/local/src/security_monkey/scripts/api-start.sh"]