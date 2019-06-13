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

import os


def env_to_bool(input):
    """
        Must change String from environment variable into Boolean
        defaults to True
    """
    if isinstance(input, str):
        if input in ('False', 'false'):
            return False
        else:
            return True
    else:
        return input


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
            'handlers': ['console'],
            'level': os.getenv('SM_CONSOLE_LOG_LEVEL', 'DEBUG')
        },
        'apscheduler': {
            'handlers': ['console'],
            'level': os.getenv('SM_APPSCHEDULER_LOG_LEVEL', 'INFO')
        }
    }
}

SQLALCHEMY_DATABASE_URI = 'postgresql://%s:%s@%s:%s/%s' % (
    os.getenv('SECURITY_MONKEY_POSTGRES_USER', 'postgres'),
    os.getenv('SECURITY_MONKEY_POSTGRES_PASSWORD', 'securitymonkeypassword'),
    os.getenv('SECURITY_MONKEY_POSTGRES_HOST', 'localhost'),
    os.getenv('SECURITY_MONKEY_POSTGRES_PORT', 5432),
    os.getenv('SECURITY_MONKEY_POSTGRES_DATABASE', 'secmonkey')
)

ENVIRONMENT = 'ec2'
USE_ROUTE53 = False
FQDN = os.getenv('SECURITY_MONKEY_FQDN', 'ec2-XX-XXX-XXX-XXX.compute-1.amazonaws.com')
API_PORT = '5000'
WEB_PORT = '443'
WEB_PATH = '/static/ui.html'
FRONTED_BY_NGINX = True
NGINX_PORT = '443'
BASE_URL = 'https://{}/'.format(FQDN)

SECRET_KEY = os.getenv('SECURITY_MONKEY_SECRET_KEY', '<INSERT_RANDOM_STRING_HERE>')

MAIL_DEFAULT_SENDER = os.getenv('SECURITY_MONKEY_EMAIL_DEFAULT_SENDER', 'securitymonkey@example.com')
SECURITY_REGISTERABLE = env_to_bool(os.getenv('SECURITY_MONKEY_SECURITY_REGISTERABLE', False))
SECURITY_CONFIRMABLE = env_to_bool(os.getenv('SECURITY_MONKEY_SECURITY_CONFIRMABLE', False))
SECURITY_RECOVERABLE = env_to_bool(os.getenv('SECURITY_MONKEY_SECURITY_RECOVERABLE', False))
SECURITY_PASSWORD_HASH = 'bcrypt'
SECURITY_PASSWORD_SALT = os.getenv('SECURITY_MONKEY_SECURITY_PASSWORD_SALT', '<INSERT_RANDOM_STRING_HERE>')
SECURITY_TRACKABLE = True

SECURITY_POST_LOGIN_VIEW = BASE_URL
SECURITY_POST_REGISTER_VIEW = BASE_URL
SECURITY_POST_CONFIRM_VIEW = BASE_URL
SECURITY_POST_RESET_VIEW = BASE_URL
SECURITY_POST_CHANGE_VIEW = BASE_URL

# This address gets all change notifications (i.e. 'securityteam@example.com')
SECURITY_TEAM_EMAIL = os.getenv('SECURITY_MONKEY_SECURITY_TEAM_EMAIL', [])

# If you would prefer the email reports to exclude justified issues, set this to False
EMAIL_AUDIT_REPORTS_INCLUDE_JUSTIFIED = env_to_bool(os.getenv('SECURITY_MONKEY_EMAIL_AUDIT_REPORTS_INCLUDE_JUSTIFIED', True))

# These are only required if using SMTP instead of SES
EMAILS_USE_SMTP = env_to_bool(os.getenv('SECURITY_MONKEY_SMTP', True))     # Otherwise, Use SES
SES_REGION = os.getenv('SECURITY_MONKEY_SES_REGION', 'us-east-1')
MAIL_SERVER = os.getenv('SECURITY_MONKEY_EMAIL_SERVER', 'smtp.example.com')
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = os.getenv('SECURITY_MONKEY_EMAIL_USERNAME', 'username')
MAIL_PASSWORD = os.getenv('SECURITY_MONKEY_EMAIL_PASSWORD', 'password')

WTF_CSRF_ENABLED = env_to_bool(os.getenv('SM_WTF_CSRF_ENABLED', True))
# Checks Referer Header. Set to False for API access.
WTF_CSRF_SSL_STRICT = env_to_bool(os.getenv('SM_WTF_CSRF_SSL_STRICT', True))
WTF_CSRF_METHODS = ['DELETE', 'POST', 'PUT', 'PATCH']

# "NONE", "SUMMARY", or "FULL"
SECURITYGROUP_INSTANCE_DETAIL = 'FULL'

# SSO SETTINGS:
ACTIVE_PROVIDERS = []  # "ping", "google", "okta" or "onelogin"
if os.getenv('SECURITY_MONKEY_ACTIVE_PROVIDERS'):
    ACTIVE_PROVIDERS = [ os.getenv('SECURITY_MONKEY_ACTIVE_PROVIDERS') ]

PING_NAME = ''  # Use to override the Ping name in the UI.
PING_REDIRECT_URI = "{BASE}api/1/auth/ping".format(BASE=BASE_URL)
PING_CLIENT_ID = ''  # Provided by your administrator
PING_AUTH_ENDPOINT = ''  # Often something ending in authorization.oauth2
PING_ACCESS_TOKEN_URL = ''  # Often something ending in token.oauth2
PING_USER_API_URL = ''  # Often something ending in idp/userinfo.openid
PING_JWKS_URL = ''  # Often something ending in JWKS
PING_SECRET = ''  # Provided by your administrator

GOOGLE_CLIENT_ID = os.getenv('SECURITY_MONKEY_GOOGLE_CLIENT_ID', '')
GOOGLE_AUTH_ENDPOINT = os.getenv('SECURITY_MONKEY_GOOGLE_AUTH_ENDPOINT', '')
GOOGLE_SECRET = os.getenv('SECURITY_MONKEY_GOOGLE_SECRET', '')
GOOGLE_HOSTED_DOMAIN = os.getenv('SECURITY_MONKEY_GOOGLE_HOSTED_DOMAIN', '') # Verify that token issued by comes from domain
# Details about domain-wide-delegation https://developers.google.com/admin-sdk/directory/v1/guides/delegation
GOOGLE_DOMAIN_WIDE_DELEGATION_KEY_PATH = os.getenv('SECURITY_MONKEY_GOOGLE_DOMAIN_WIDE_DELEGATION_KEY_PATH', '') # path to service account key with enabled domain wide delegation
GOOGLE_DOMAIN_WIDE_DELEGATION_KEY_JSON = os.getenv('SECURITY_MONKEY_GOOGLE_DOMAIN_WIDE_DELEGATION_KEY_JSON', '') # json of service account key with enabled domain wide delegation
GOOGLE_ADMIN_ROLE_GROUP_NAME = '' # Google group name which should map to security-monkey role Admin
GOOGLE_AUTH_API_METHOD = 'People' # alternative 'Directory' to use Google SSO against Directory API
GOOGLE_DOMAIN_WIDE_DELEGATION_SUBJECT = '' # perform google directory api calls as the this subject 

OKTA_NAME = os.getenv('SECURITY_MONKEY_OKTA_NAME', 'Okta')   # Used to override the Okta name in the UI.
OKTA_AUTH_SERVER = os.getenv('SECURITY_MONKEY_OKTA_AUTH_SERVER', 'default')   # Your Okta Authentication Server name, in no custom this is likely 'default'.
OKTA_BASE_URL = os.getenv('SECURITY_MONKEY_OKTA_BASE_URL', '')   # Your Okta account endpoint
OKTA_AUTH_ENDPOINT = '{OKTA_BASE}/oauth2/{AUTH_SERVER}/v1/authorize'.format(OKTA_BASE=OKTA_BASE_URL, AUTH_SERVER=OKTA_AUTH_SERVER)
OKTA_TOKEN_ENDPOINT = '{OKTA_BASE}/oauth2/{AUTH_SERVER}/v1/token'.format(OKTA_BASE=OKTA_BASE_URL, AUTH_SERVER=OKTA_AUTH_SERVER)
OKTA_USER_INFO_ENDPOINT = '{OKTA_BASE}/oauth2/{AUTH_SERVER}/v1/userinfo'.format(OKTA_BASE=OKTA_BASE_URL, AUTH_SERVER=OKTA_AUTH_SERVER)
OKTA_JWKS_URI = '{OKTA_BASE}/oauth2/{AUTH_SERVER}/v1/keys'.format(OKTA_BASE=OKTA_BASE_URL, AUTH_SERVER=OKTA_AUTH_SERVER)
OKTA_CLIENT_ID = os.getenv('SECURITY_MONKEY_OKTA_CLIENT_ID', '')   # Retrieved from the Okta Admin panel, under the Application.
OKTA_CLIENT_SECRET = os.getenv('SECURITY_MONKEY_OKTA_CLIENT_SECRET', '')   # Retrieved from the Okta Admin panel, under the Application.
OKTA_REDIRECT_URI = '{BASE}/api/1/auth/okta'.format(BASE=BASE_URL)
OKTA_DEFAULT_ROLE = os.getenv('SECURITY_MONKEY_OKTA_DEFAULT_ROLE', 'View')

ONELOGIN_APP_ID = os.getenv('SECURITY_MONKEY_ONELOGIN_APP_ID', '<APP_ID>')  # OneLogin App ID provider by your administrator
ONELOGIN_EMAIL_FIELD = os.getenv('SECURITY_MONKEY_ONELOGIN_EMAIL_FIELD', 'User.email')  # SAML attribute used to provide email address
ONELOGIN_DEFAULT_ROLE = 'View'  # Default RBAC when user doesn't already exist
ONELOGIN_HTTPS = True  # If using HTTPS strict mode will check the requests are HTTPS
ONELOGIN_IDP_CERT = os.getenv('SECURITY_MONKEY_ONELOGIN_IDP_CERT', '<IDP_CERT>')
ONELOGIN_USE_CUSTOM = os.getenv('SECURITY_MONKEY_ONELOGIN_USE_CUSTOM', False)
if not ONELOGIN_USE_CUSTOM:
    ONELOGIN_ENTITY_ID = "https://app.onelogin.com/saml/metadata/{APP_ID}".format(APP_ID=ONELOGIN_APP_ID)
    ONELOGIN_SSO_URL = "https://app.onelogin.com/trust/saml2/http-post/sso/{APP_ID}".format(APP_ID=ONELOGIN_APP_ID)
    ONELOGIN_SLO_URL = "https://app.onelogin.com/trust/saml2/http-redirect/slo/{APP_ID}".format(APP_ID=ONELOGIN_APP_ID)
else:
    ONELOGIN_ENTITY_ID = os.getenv('SECURITY_MONKEY_ONELOGIN_ENTITY_ID')
    ONELOGIN_SSO_URL = os.getenv('SECURITY_MONKEY_ONELOGIN_SSO_URL')
    ONELOGIN_SLO_URL = os.getenv('SECURITY_MONKEY_ONELOGIN_SLO_URL')
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
        "entityId": ONELOGIN_ENTITY_ID,
        # SSO endpoint info of the IdP. (Authentication Request protocol)
        "singleSignOnService": {
            # URL Target of the IdP where the Authentication Request Message
            # will be sent.
            "url": ONELOGIN_SSO_URL,
            # SAML protocol binding to be used when returning the <Response>
            # message. OneLogin Toolkit supports the HTTP-Redirect binding
            # only for this endpoint.
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        # SLO endpoint info of the IdP.
        "singleLogoutService": {
            # URL Location of the IdP where SLO Request will be sent.
            "url": ONELOGIN_SLO_URL,
            # SAML protocol binding to be used when returning the <Response>
            # message. OneLogin Toolkit supports the HTTP-Redirect binding
            # only for this endpoint.
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        # Public x509 certificate of the IdP
        "x509cert": ONELOGIN_IDP_CERT
    }
}

from datetime import timedelta
PERMANENT_SESSION_LIFETIME=timedelta(minutes=60)
SESSION_REFRESH_EACH_REQUEST=True
SESSION_COOKIE_SECURE=env_to_bool(os.getenv('SESSION_COOKIE_SECURE', True))
SESSION_COOKIE_HTTPONLY=True
PREFERRED_URL_SCHEME='https'

REMEMBER_COOKIE_DURATION=timedelta(minutes=60)  # Can make longer if you want remember_me to be useful.
REMEMBER_COOKIE_SECURE=True
REMEMBER_COOKIE_HTTPONLY=True

# Header auth allows you to trust a header set by a reverse proxy to
# authenticate the current user. This is useful if you have an authn
# wall in front of your intranet that already knows the identity of
# the requester and can pass it along to Security Monkey.
USE_HEADER_AUTH=env_to_bool(os.getenv("SECURITY_MONKEY_USE_HEADER_AUTH", False))
HEADER_AUTH_USERNAME_HEADER=os.getenv("SECURITY_MONKEY_HEADER_AUTH_USERNAME_HEADER", "Remote-User")
HEADER_AUTH_GROUPS_HEADER=os.getenv("SECURITY_MONKEY_HEADER_AUTH_GROUPS_HEADER")

# Log SSL Cert SubjectAltName errors
LOG_SSL_SUBJ_ALT_NAME_ERRORS = True
