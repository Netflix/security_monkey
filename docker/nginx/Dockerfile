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

FROM nginx:1.11.4
MAINTAINER Netflix Open Source Development <talent@netflix.com>

ENV SECURITY_MONKEY_VERSION=v0.8.0
RUN apt-get update &&\
  apt-get install -y curl git sudo apt-transport-https &&\
  curl https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - &&\
  curl https://storage.googleapis.com/download.dartlang.org/linux/debian/dart_stable.list > /etc/apt/sources.list.d/dart_stable.list && \
  apt-get update &&\
  apt-get install -y -q dart &&\
  rm -rf /var/lib/apt/lists/*

RUN cd /usr/local/src &&\
  mkdir -p security_monkey
ADD . /usr/local/src/security_monkey

RUN cd /usr/local/src/security_monkey/dart &&\
  /usr/lib/dart/bin/pub get &&\
  /usr/lib/dart/bin/pub build &&\
  /bin/mkdir -p /usr/local/src/security_monkey/security_monkey/static/ &&\
  /bin/cp -R /usr/local/src/security_monkey/dart/build/web/* /usr/local/src/security_monkey/security_monkey/static/

RUN /bin/rm /etc/nginx/conf.d/default.conf &&\
  /bin/mkdir -p /var/log/security_monkey/ /etc/nginx/ssl/ &&\
  ln -s /dev/stdout /var/log/security_monkey/security_monkey.access.log &&\
  ln -s /dev/stderr /var/log/security_monkey/security_monkey.error.log

WORKDIR /etc/nginx
EXPOSE 443

ADD docker/nginx/conf.d/securitymonkey.conf /etc/nginx/conf.d/securitymonkey.conf
COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf

ENTRYPOINT ["/usr/local/src/security_monkey/docker/nginx/start-nginx.sh"]
