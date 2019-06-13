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

FROM nginx:stable
MAINTAINER Netflix Open Source Development <talent@netflix.com>

ENV SECURITY_MONKEY_VERSION=v1.1.3
RUN apt-get update &&\
  apt-get install -y curl git sudo unzip
RUN curl -s https://storage.googleapis.com/dart-archive/channels/stable/release/1.24.3/sdk/dartsdk-linux-x64-release.zip > dartsdk.zip
RUN unzip -qq /dartsdk.zip -d /opt/google
RUN rm /dartsdk.zip
RUN mv /opt/google/dart-sdk* /opt/google/dart

RUN cd /usr/local/src &&\
  mkdir -p security_monkey

COPY dart /usr/local/src/security_monkey/dart

RUN cd /usr/local/src/security_monkey/dart &&\
  /opt/google/dart/bin/pub get && \
  /opt/google/dart/bin/pub build && \
  /bin/mkdir -p /usr/local/src/security_monkey/security_monkey/static/ && \
  /bin/cp -R /usr/local/src/security_monkey/dart/build/web/* /usr/local/src/security_monkey/security_monkey/static/ && \
  rm -r /usr/local/src/security_monkey/dart/build

RUN /bin/rm /etc/nginx/conf.d/default.conf &&\
  /bin/mkdir -p /var/log/security_monkey/ /etc/nginx/ssl/ &&\
  chmod -R guo+r /usr/local/src/security_monkey &&\
  find /usr/local/src/security_monkey -type d -exec chmod 755 {} \;

WORKDIR /etc/nginx
EXPOSE 443

COPY docker/nginx/conf.d/securitymonkey.conf /etc/nginx/conf.d/securitymonkey.conf
COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf
COPY docker /usr/local/src/security_monkey/docker

ENTRYPOINT ["/usr/local/src/security_monkey/docker/nginx/start-nginx.sh"]
