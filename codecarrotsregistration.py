__author__ = 'Piotr Dyba'

from os import path

from flask import Flask
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug.debug import DebuggedApplication
from flask.ext.bcrypt import Bcrypt


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


def make_app(debug=False):
    """
    Create and configure Flask app.
    """

    # cfg = path.join(
    #     path.dirname(path.realpath(__file__)),
    #     "deploy.cfg",
    # )
    # app.config.from_pyfile(cfg)
    app.debug = True
    app.static_path = path.join(path.abspath(__file__), 'static')

    init_admin()
    mail.init_app(app)
    if debug:
        return DebuggedApplication(app, evalex=True)
    return app





app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "IT_IS_A_SECRET"
db = SQLAlchemy()
db.app = app
db.init_app(app)
admin = Admin(app)
mail = Mail()
lm = LoginManager()
lm.init_app(app)
bcrypt = Bcrypt()


if __name__ == '__main__':
    app = make_app(debug=True)
    if not User.query.first():
        from init_db import db_start
        db_start()
    from views import *
    app.run(debug=True)

