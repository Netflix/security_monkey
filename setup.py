#     Copyright 2018 Netflix, Inc.
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
import ast
import re

from setuptools import find_packages, setup

_version_re = re.compile(r'__version__\s+=\s+(.*)')
with open('security_monkey/__init__.py', 'rb') as f:
    SECURITY_MONKEY_VERSION = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='security_monkey',
    version=SECURITY_MONKEY_VERSION,
    long_description=__doc__,
    packages=find_packages(exclude=["tests"]),
    package_data={
        'security_monkey': [
            'templates/*.json',
            'templates/*.html',
            'templates/security/*.html',
        ]
    },
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    data_files=[('env-config', ['env-config/config.py',
                                'env-config/config-docker.py']),
                ('data', ['data/aws_accounts.json'])],
    zip_safe=False,
    install_requires=[
        'six>=1.11.0',
        'cloudaux==1.4.10',
        'celery==4.1.0',
        'celery[redis]==4.1.0',
        'redis==2.10.6',
        'Flask>=0.12.2',
        'Flask-Mail==0.9.1',
        'Flask-Migrate==2.1.1',
        'Flask-Principal==0.4.0',
        'Flask-RESTful==0.3.6',
        'Flask-SQLAlchemy==1.0',
        'Flask-Script==0.6.3',
        'Flask-Security>=3.0.0',
        'Flask-WTF>=0.14.2',
        'Jinja2>=2.10',
        'SQLAlchemy==1.2.5',
        'boto>=2.48.0',
        'ipaddr==2.2.0',
        'itsdangerous==0.24',
        'psycopg2==2.7.4',
        'bcrypt==3.1.4',
        'gunicorn==19.7.1',
        'cryptography>=1.8.1',
        'dpath==1.4.2',
        'pyyaml>=3.12',
        'jira==1.0.14',
        'policyuniverse>=1.1.0.1',
        'joblib>=0.9.4',
        'pyjwt>=1.01',
        'netaddr',
        'swag-client>=0.3.7',
        'idna==2.6'
    ],
    extras_require={
        'onelogin': ['python-saml>=2.4.0'],
        'sentry': ['raven[flask]==6.6.0'],
        'tests': [
            'pytest==3.4.2',
            'nose==1.3.7',
            'mixer==6.0.1',
            'mock==2.0.0',
            'moto==0.4.30',
            'freezegun>=0.3.7',
            'testtools==2.3.0'
        ]
    },
    entry_points={
        'console_scripts': [
            'monkey = security_monkey.manage:main',
        ],
    }
)
