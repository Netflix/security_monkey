#!/bin/bash
##########################################
#     Copyright 2015 Netflix, Inc.
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
##########################################
#
# Script to test Dart installation for Security Monkey
#
##########################################

DART_DOWNLOAD_LOCATION="https://storage.googleapis.com/dart-archive/channels/stable/release/1.16.1/sdk/dartsdk-linux-x64-release.zip"

echo "Getting Dart..."
wget $DART_DOWNLOAD_LOCATION -O 'dartsdk-linux-x64-release.zip'

echo "Unzipping Dart..."
unzip "dartsdk-linux-x64-release.zip" > /dev/null

echo Setting up the environment variables
export DART_SDK="$PWD/dart-sdk"
export PATH="$DART_SDK/bin:$PATH"

echo "Building the dart deps..."
cd dart
pub get
pub build --mode=debug
