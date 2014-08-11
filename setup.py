#     Copyright 2014 Netflix, Inc.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
import os
from setuptools import setup

setup(
    name='security_monkey',
    version='0.0.1',
    long_description=__doc__,
    packages=['security_monkey'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
            'APScheduler==2.1.2',
            'BeautifulSoup==3.2.1',
            'Flask==0.10.1',
            'Flask-Login==0.2.10',
            'Flask-Mail==0.9.0',
            'Flask-Migrate==1.2.0',
            'Flask-Principal==0.4.0',
            'Flask-RESTful==0.2.5',
            'Flask-SQLAlchemy==1.0',
            'Flask-Script==0.6.3',
            'Flask-Security==1.7.3',
            'Flask-WTF==0.9.5',
            'Jinja2==2.7.2',
            'MarkupSafe==0.18',
            'Paste==1.7.5.1',
            'SQLAlchemy==0.9.2',
            'Werkzeug==0.9.4',
            'aniso8601==0.82',
            'arrow==0.4.2',
            'boto==2.32.1',
            'bottle==0.12.3',
            'dnspython==1.11.1',
            'ipaddr==2.1.11',
            'ipython==1.2.0',
            'itsdangerous==0.23',
            'mock==1.0.1',
            'nose==1.3.0',
            'pika==0.9.13',
            'psycopg2==2.5.2',
            'python-dateutil==2.2',
            'python-memcached==1.53',
            'requests==2.2.1',
            'py-bcrypt==0.4',
            'Sphinx==1.2.2',
            'gunicorn==18.0'
    ]
)
