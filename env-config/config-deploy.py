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

LOG_CFG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'standard',
            'filename': '/var/log/security_monkey/securitymonkey.log',
            'maxBytes': 10485760,
            'backupCount': 100,
            'encoding': 'utf8'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'security_monkey': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG'
        },
        'apscheduler': {
            'handlers': ['file', 'console'],
            'level': 'INFO'
        }
    }
}

SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:securitymonkeypassword@localhost:5432/secmonkey'

SQLALCHEMY_POOL_SIZE = 50
SQLALCHEMY_MAX_OVERFLOW = 15
ENVIRONMENT = 'ec2'
USE_ROUTE53 = False
FQDN = 'ec2-XX-XXX-XXX-XXX.compute-1.amazonaws.com'
API_PORT = '5000'
WEB_PORT = '443'
WEB_PATH = '/static/ui.html'
FRONTED_BY_NGINX = True
NGINX_PORT = '443'
BASE_URL = 'https://{}/'.format(FQDN)

SECRET_KEY = '<INSERT_RANDOM_STRING_HERE>'

MAIL_DEFAULT_SENDER = 'securitymonkey@example.com'
SECURITY_REGISTERABLE = True
SECURITY_CONFIRMABLE = False
SECURITY_RECOVERABLE = False
SECURITY_PASSWORD_HASH = 'bcrypt'
SECURITY_PASSWORD_SALT = '<INSERT_RANDOM_STRING_HERE>'
SECURITY_TRACKABLE = True

SECURITY_POST_LOGIN_VIEW = BASE_URL
SECURITY_POST_REGISTER_VIEW = BASE_URL
SECURITY_POST_CONFIRM_VIEW = BASE_URL
SECURITY_POST_RESET_VIEW = BASE_URL
SECURITY_POST_CHANGE_VIEW = BASE_URL

# This address gets all change notifications (i.e. 'securityteam@example.com')
SECURITY_TEAM_EMAIL = []

# These are only required if using SMTP instead of SES
EMAILS_USE_SMTP = False     # Otherwise, Use SES
SES_REGION = 'us-east-1'
MAIL_SERVER = 'smtp.example.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = 'username'
MAIL_PASSWORD = 'password'

WTF_CSRF_ENABLED = True
WTF_CSRF_SSL_STRICT = True # Checks Referer Header. Set to False for API access.
WTF_CSRF_METHODS = ['DELETE', 'POST', 'PUT', 'PATCH']

# "NONE", "SUMMARY", or "FULL"
SECURITYGROUP_INSTANCE_DETAIL = 'FULL'

# Threads used by the scheduler.
# You will likely need at least one core thread for every account being monitored.
CORE_THREADS = 25
MAX_THREADS = 30

# SSO SETTINGS:
ACTIVE_PROVIDERS = []  # "ping" or "google"

PING_NAME = ''  # Use to override the Ping name in the UI.
PING_REDIRECT_URI = "{BASE}api/1/auth/ping".format(BASE=BASE_URL)
PING_CLIENT_ID = ''  # Provided by your administrator
PING_AUTH_ENDPOINT = ''  # Often something ending in authorization.oauth2
PING_ACCESS_TOKEN_URL = ''  # Often something ending in token.oauth2
PING_USER_API_URL = ''  # Often something ending in idp/userinfo.openid
PING_JWKS_URL = ''  # Often something ending in JWKS
PING_SECRET = ''  # Provided by your administrator

GOOGLE_CLIENT_ID = ''
GOOGLE_AUTH_ENDPOINT = ''
GOOGLE_SECRET = ''

from datetime import timedelta
PERMANENT_SESSION_LIFETIME=timedelta(minutes=60)
SESSION_REFRESH_EACH_REQUEST=True
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
PREFERRED_URL_SCHEME='https'

REMEMBER_COOKIE_DURATION=timedelta(minutes=60)  # Can make longer if you want remember_me to be useful.
REMEMBER_COOKIE_SECURE=True
REMEMBER_COOKIE_HTTPONLY=True
