FROM centos:7.2.1511

MAINTAINER Curtis Stewart <dev.stewart.curtis@dev.bwater.com>

# System deps (root)
# Lets cache this, because it takes a while
RUN yum install -y @development && yum clean all
RUN yum install -y \
        bind-utils \
        libffi-devel \
        libxml2-devel \
        libxslt-devel \
        mysql \
        mysql-devel \
        openldap-devel \
        postgresql \
        postgresql-devel \
        python-devel \
        wget \
        unzip && \
    yum clean all

RUN curl -fSL 'https://bootstrap.pypa.io/get-pip.py' | python - --no-setuptools


RUN mkdir -p /usr/src/app
WORKDIR /usr/src
RUN pip install virtualenv
RUN virtualenv -p /usr/bin/python2.7 --no-setuptools venv
RUN curl -fSL 'https://bootstrap.pypa.io/ez_setup.py' | /usr/src/venv/bin/python - --version=32.1.0
RUN /usr/src/venv/bin/pip install pytest flake8 signalfx

RUN mkdir -p /var/log/security_monkey
RUN touch /var/log/security_monkey/security_monkey-dump.log

WORKDIR /usr/src/app
COPY . /usr/src/app

ENV SECURITY_MONKEY_SETTINGS /usr/src/app/ci/config-ci.py

CMD /usr/src/app/ci/sm_test.sh
