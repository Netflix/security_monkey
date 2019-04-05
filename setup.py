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

with open('requirements.txt') as f:
    INSTALL_REQUIRED = f.read().splitlines()

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
    install_requires=INSTALL_REQUIRED,
    extras_require={
        'onelogin': ['python-saml>=2.4.0'],
        'sentry': ['raven[flask]==6.6.0'],
        'googleauth': ['google-auth'],
        'tests': [
            'pytest==3.4.2',
            'nose==1.3.7',
            'mixer==6.0.1',
            'mock==2.0.0',
            'freezegun>=0.3.7',
            'testtools==2.3.0',
            'requests_mock==1.5.2',
            'oslotest==3.7.0',
            'moto @ git+https://github.com/spulec/moto.git#egg=moto'
        ]
    },
    entry_points={
        'console_scripts': [
            'monkey = security_monkey.manage:main',
        ],
    }
)
