from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()

from flask_login import LoginManager
lm = LoginManager()

from flask_mail import Mail
mail = Mail()

from .auth.modules import RBAC
rbac = RBAC()

# JiraSync -- will be set inside of factories.py
js = None
