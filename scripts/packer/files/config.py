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
# Insert any config items here.
# This will be fed into Flask/SQLAlchemy inside security_monkey/__init__.py

LOG_LEVEL = "APP_LOG_LEVEL"
LOG_FILE = "APP_LOG_DIR/APP_LOG_FILE"

SQLALCHEMY_DATABASE_URI = 'postgresql://APP_DB_USERNAME:APP_DB_PASSWORD@APP_DB_ENDPOINT/APP_DB_SCHEMA'

SQLALCHEMY_POOL_SIZE = APP_DB_POOL_SIZE
SQLALCHEMY_MAX_OVERFLOW = APP_DB_MAX_OVERFLOW
ENVIRONMENT = 'APP_ENVIRONMENT'
USE_ROUTE53 = APP_USE_ROUTE53
FQDN = 'APP_FQDN'
API_PORT = APP_API_PORT
WEB_PORT = APP_WEB_PORT
WEB_PATH = 'APP_WEB_PATH'
FRONTED_BY_NGINX = APP_USE_NGINX
NGINX_PORT = APP_NGINX_PORT
BASE_URL = 'APP_BASE_URL_FORMAT'.format(FQDN)

SECRET_KEY = 'APP_SECRET_KEY'

SECURITY_REGISTERABLE = APP_SEC_REGISTER
SECURITY_CONFIRMABLE = APP_SEC_CONFIRM
SECURITY_RECOVERABLE = APP_SEC_RECOVER
SECURITY_PASSWORD_HASH = 'APP_SEC_PW_HASH'
SECURITY_PASSWORD_SALT = 'APP_SEC_PW_SALT'

SECURITY_POST_LOGIN_VIEW = BASE_URL
SECURITY_POST_REGISTER_VIEW = BASE_URL
SECURITY_POST_CONFIRM_VIEW = BASE_URL
SECURITY_POST_RESET_VIEW = BASE_URL
SECURITY_POST_CHANGE_VIEW = BASE_URL

# This address gets all change notifications (i.e. 'securityteam@example.com')
SECURITY_TEAM_EMAIL = [APP_SEC_TEAM_EMAILS]

# These are only required if using SMTP instead of SES
EMAILS_USE_SMTP = APP_MAIL_USE_SMTP
SES_REGION = 'APP_MAIL_SES_REGION'
MAIL_DEFAULT_SENDER = 'APP_MAIL_DEFAULT_SENDER'
MAIL_SERVER = 'APP_MAIL_SERVER'
MAIL_PORT = APP_MAIL_PORT
MAIL_USE_SSL = APP_MAIL_USE_SSL
MAIL_USERNAME = 'APP_MAIL_USERNAME'
MAIL_PASSWORD = 'APP_MAIL_PASSWORD'

WTF_CSRF_ENABLED = APP_WTF_CSRF_ENABLED
WTF_CSRF_SSL_STRICT = APP_WTF_CSRF_STRICT
WTF_CSRF_METHODS = [APP_WTF_CSRF_METHODS]

# "NONE", "SUMMARY", or "FULL"
SECURITYGROUP_INSTANCE_DETAIL = 'APP_INSTANCE_DETAIL'

# Threads used by the scheduler.
# You will likely need at least one core thread for every account being monitored.
CORE_THREADS = APP_CORE_THREADS
MAX_THREADS = APP_MAX_THREADS
