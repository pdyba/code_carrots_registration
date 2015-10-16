__author__ = 'Piotr Dyba'

from os import path

from flask import Flask
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.login import LoginManager, current_user
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt


app = Flask(__name__)
cfg = path.join(
    path.dirname(path.realpath(__file__)),
    "deploy.cfg",
)
app.config.from_pyfile(cfg)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "IT_IS_A_SECRET"
db = SQLAlchemy()
db.app = app
db.init_app(app)
admin = Admin(app)
mail = Mail(app)
lm = LoginManager()
lm.init_app(app)
bcrypt = Bcrypt()


class AdminModelViewWithAuth(ModelView):
    """
    ModelView with authentication.
    """
    def is_accessible(self):
        """
        Return True when user can access Admin.
        """
        return not current_user.is_anonymous() and current_user.is_admin()


def init_admin():
    """
    Expose some of models in Admin.
    """
    from models import User
    admin.add_view(AdminModelViewWithAuth(User, db.session))
    return admin


def make_app(debug=False):
    """
    Create and configure Flask app.
    """
    app.debug = debug
    app.static_path = path.join(path.abspath(__file__), 'static')
    mail.init_app(app)
    init_admin()
    from models import User
    try:
        User.query.first()
    except:
        from init_db import db_start
        db_start()
    from views import *
    return app


if __name__ == '__main__':
    app = make_app(debug=True)
    app.run(debug=True)
