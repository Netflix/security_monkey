from security_monkey import app
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)

from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()
