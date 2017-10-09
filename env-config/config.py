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
            # 'class': 'logging.handlers.RotatingFileHandler',
            'class': 'logging.handlers.GroupWriteRotatingFileHandler',
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
            'level': 'WARN'
        },
        'apscheduler': {
            'handlers': ['file', 'console'],
            'level': 'INFO'
        }
    }
}

# If this Monkey is watching AWS Govcloud, set this to TRUE.
# Best practice will only allow Govcloud Accounts to watch other Govcloud Accounts
# and Commercial Accounts to watch Commercial Accounts. They should not mix.

AWS_GOVCLOUD = False


SQLALCHEMY_DATABASE_URI = 'postgresql://securitymonkeyuser:securitymonkeypassword@localhost:5432/secmonkey'

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
SECURITY_REGISTERABLE = False
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
ACTIVE_PROVIDERS = []  # "aad", "ping", "google" or "onelogin"

AAD_NAME = 'AzureAD'  # Use to override the Ping name in the UI.
AAD_REDIRECT_URI = "{BASE}api/1/auth/aad".format(BASE=BASE_URL)
AAD_CLIENT_ID = '' # Azure AD application client ID
AAD_AUTH_ENDPOINT = 'https://login.microsoftonline.com/<tenant>/oauth2/authorize' # Replace <tenant> with the Azure AD tenant ID
AAD_JWKS_URL = 'https://login.microsoftonline.com/common/discovery/keys'
AAD_DEFAULT_ROLE = 'View'


PING_NAME = ''  # Use to override the Ping name in the UI.
PING_REDIRECT_URI = "{BASE}api/1/auth/ping".format(BASE=BASE_URL)
PING_CLIENT_ID = ''  # Provided by your administrator
PING_AUTH_ENDPOINT = ''  # Often something ending in authorization.oauth2
PING_ACCESS_TOKEN_URL = ''  # Often something ending in token.oauth2
PING_USER_API_URL = ''  # Often something ending in idp/userinfo.openid
PING_JWKS_URL = ''  # Often something ending in JWKS
PING_SECRET = ''  # Provided by your administrator
PING_DEFAULT_ROLE = 'View'

GOOGLE_CLIENT_ID = ''
GOOGLE_AUTH_ENDPOINT = ''
GOOGLE_SECRET = ''
# GOOGLE_HOSTED_DOMAIN = 'example.com' # Verify that token issued by comes from domain
GOOGLE_DEFAULT_ROLE = 'View'

ONELOGIN_APP_ID = '<APP_ID>'  # OneLogin App ID provider by your administrator
ONELOGIN_EMAIL_FIELD = 'User.email'  # SAML attribute used to provide email address
ONELOGIN_DEFAULT_ROLE = 'View'  # Default RBAC when user doesn't already exist
ONELOGIN_HTTPS = True  # If using HTTPS strict mode will check the requests are HTTPS
ONELOGIN_SETTINGS = {
    # If strict is True, then the Python Toolkit will reject unsigned
    # or unencrypted messages if it expects them to be signed or encrypted.
    # Also it will reject the messages if the SAML standard is not strictly
    # followed. Destination, NameId, Conditions ... are validated too.
    "strict": True,

    # Enable debug mode (outputs errors).
    "debug": True,

    # Service Provider Data that we are deploying.
    "sp": {
        # Identifier of the SP entity  (must be a URI)
        "entityId": "{BASE}metadata/".format(BASE=BASE_URL),
        # Specifies info about where and how the <AuthnResponse> message MUST be
        # returned to the requester, in this case our SP.
        "assertionConsumerService": {
            # URL Location where the <Response> from the IdP will be returned
            "url": "{BASE}api/1/auth/onelogin?acs".format(BASE=BASE_URL),
            # SAML protocol binding to be used when returning the <Response>
            # message. OneLogin Toolkit supports this endpoint for the
            # HTTP-POST binding only.
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        },
        # If you need to specify requested attributes, set a
        # attributeConsumingService. nameFormat, attributeValue and
        # friendlyName can be omitted
        #"attributeConsumingService": {
        #        "ServiceName": "SP test",
        #        "serviceDescription": "Test Service",
        #        "requestedAttributes": [
        #            {
        #                "name": "",
        #                "isRequired": False,
        #                "nameFormat": "",
        #                "friendlyName": "",
        #                "attributeValue": ""
        #            }
        #        ]
        #},
        # Specifies info about where and how the <Logout Response> message MUST be
        # returned to the requester, in this case our SP.
        "singleLogoutService": {
            # URL Location where the <Response> from the IdP will be returned
            "url": "{BASE}api/1/auth/onelogin?sls".format(BASE=BASE_URL),
            # SAML protocol binding to be used when returning the <Response>
            # message. OneLogin Toolkit supports the HTTP-Redirect binding
            # only for this endpoint.
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        # Specifies the constraints on the name identifier to be used to
        # represent the requested subject.
        # Take a look on src/onelogin/saml2/constants.py to see the NameIdFormat that are supported.
        "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
        # Usually x509cert and privateKey of the SP are provided by files placed at
        # the certs folder. But we can also provide them with the following parameters
        "x509cert": "",
        "privateKey": ""
    },

    # Identity Provider Data that we want connected with our SP.
    "idp": {
        # Identifier of the IdP entity  (must be a URI)
        "entityId": "https://app.onelogin.com/saml/metadata/{APP_ID}".format(APP_ID=ONELOGIN_APP_ID),
        # SSO endpoint info of the IdP. (Authentication Request protocol)
        "singleSignOnService": {
            # URL Target of the IdP where the Authentication Request Message
            # will be sent.
            "url": "https://app.onelogin.com/trust/saml2/http-post/sso/{APP_ID}".format(APP_ID=ONELOGIN_APP_ID),
            # SAML protocol binding to be used when returning the <Response>
            # message. OneLogin Toolkit supports the HTTP-Redirect binding
            # only for this endpoint.
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        # SLO endpoint info of the IdP.
        "singleLogoutService": {
            # URL Location of the IdP where SLO Request will be sent.
            "url": "https://app.onelogin.com/trust/saml2/http-redirect/slo/{APP_ID}".format(APP_ID=ONELOGIN_APP_ID),
            # SAML protocol binding to be used when returning the <Response>
            # message. OneLogin Toolkit supports the HTTP-Redirect binding
            # only for this endpoint.
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        # Public x509 certificate of the IdP
        "x509cert": "<ONELOGIN_APP_CERT>"
    }
}

from datetime import timedelta
PERMANENT_SESSION_LIFETIME=timedelta(minutes=60)
SESSION_REFRESH_EACH_REQUEST=True
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
PREFERRED_URL_SCHEME='https'

REMEMBER_COOKIE_DURATION=timedelta(minutes=60)  # Can make longer if you want remember_me to be useful.
REMEMBER_COOKIE_SECURE=True
REMEMBER_COOKIE_HTTPONLY=True

# Apscheduler Configurations
# Length of time, in seconds, before a scheduled job is cancelled due to thread contention or other issues
MISFIRE_GRACE_TIME=30
# Delay, in seconds, until reporter starts
REPORTER_START_DELAY=10

# JIRA Settings
# Verify JIRA SSL certs - useful for testing on JIRA sandbox server
JIRA_SSL_VERIFY = True
JIRA_OPEN = 'Open' # Opened ticket JIRA transition name (e.g. 'Open', 'To Do')
JIRA_CLOSED = 'Closed' # Closed ticket JIRA transition name (e.g. 'Closed', 'Done')
