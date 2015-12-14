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
from __future__ import absolute_import

import sys
import shutil
import os.path
import zipfile
import platform

from distutils import log
from distutils.core import Command
from setuptools.command.develop import develop
from setuptools.command.install import install
from setuptools.command.sdist import sdist
from setuptools import setup, find_packages
from subprocess import check_output

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))

# When executing the setup.py, we need to be able to import ourselves, this
# means that we need to add the src/ directory to the sys.path.
sys.path.insert(0, ROOT)

about = {}
with open(os.path.join(ROOT, "security_monkey", "__about__.py")) as f:
    exec(f.read(), about)

install_requires = open('requirements.txt', 'r').read().split()

tests_require = []

docs_require = []

dev_requires = [
    'invoke'
]


class SmartInstall(install):
    """
    Installs Lemur into the Python environment.
    If the package indicator is missing, this will also force a run of
    `build_static` which is required for JavaScript assets and other things.
    """
    def _needs_static(self):
        return not os.path.exists(os.path.join(ROOT, 'security_monkey/static/'))

    def run(self):
        if self._needs_static():
            self.run_command('build_static')
        install.run(self)


class DevelopWithBuildStatic(develop):
    def install_for_development(self):
        self.run_command('build_static')
        return develop.install_for_development(self)


class SdistWithBuildStatic(sdist):
    def make_release_tree(self, *a, **kw):
        dist_path = self.distribution.get_fullname()

        sdist.make_release_tree(self, *a, **kw)

        self.reinitialize_command('build_static', work_path=dist_path)
        self.run_command('build_static')


class BuildStatic(Command):
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if platform.system() == 'Darwin':
            dart_path = install_dart_osx()
        else:
            dart_path = install_dart_debian()

        dart_source = os.path.join(ROOT, 'dart')
        log.info("running [dart pub] in {0} with {1}".format(dart_source, dart_path))
        try:
            check_output([dart_path, 'get'], cwd=dart_source)
            log.info("running [dart build] in {0} from {1}".format(dart_source, dart_path))
            check_output([dart_path, 'build'], cwd=dart_source)
            os.mkdir(os.path.join(ROOT, 'security_monkey/static'))
            shutil.move(os.path.join(dart_source, 'build/web'), os.path.join(ROOT, 'security_monkey/static'))
        except Exception as e:
            log.warn("Unable to build static content: {0}".format(e))


def install_dart_osx():
    """
    Installation steps for dart on OS X
    :return:
    """
    log.info("getting required dependencies for OS X")
    check_output(['curl', 'https://storage.googleapis.com/dart-archive/channels/stable/release/1.12.1/sdk/dartsdk-macos-x64-release.zip', '--output', 'dart.zip'])
    with zipfile.ZipFile('dart.zip', 'r') as z:
        z.extractall(ROOT)
    bin = os.path.join(ROOT, 'dart-sdk', 'bin')
    for r, d, files in os.walk(bin):
        for f in files:
            try:
                os.chmod(os.path.join(bin, f), 0777)
            except os.error:
                log.warn("skipping... {0}".format(f))
    return os.path.join(bin, 'pub')


def install_dart_debian():
    """
    Installation steps for dart on debian
    :return:
    """
    log.info("getting required dependencies for debian")
    # do we care that these are curls?
    check_output(['curl', 'https://dl-ssl.google.com/linux/linux_signing_key.pub'])
    check_output(['sudo', 'apt-get', 'add', '-'])
    shutil.move('dart_stable.list', '/etc/apt/sources.list.d/dart_stable.list')
    check_output(['sudo', 'apt-get', 'update'])
    check_output(['sudo', 'apt-get', 'install', '-y', 'dart=1.12.2-1'])
    return '/usr/lib/dart/bin/pub'


setup(
    name=about["__title__"],
    version=about["__version__"],
    author=about["__author__"],
    author_email=about["__email__"],
    url=about["__uri__"],
    description=about["__summary__"],
    long_description=open(os.path.join(ROOT, 'README.rst')).read(),
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'tests': tests_require,
        'docs': docs_require,
        'dev': dev_requires,
    },
    cmdclass={
        'build_static': BuildStatic,
        'sdist': SdistWithBuildStatic,
        'install': SmartInstall
    },
    entry_points={
        'console_scripts': [
            'securitymonkey = security_monkey.manage:main',
        ]
    },
    classifiers=[
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        "Programming Language :: Python :: 2.7",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License"
    ]
)

