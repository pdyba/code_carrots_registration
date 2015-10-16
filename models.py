__author__ = 'Piotr Dyba'

from datetime import datetime

from flask.ext.login import UserMixin

from sqlalchemy import Column
from sqlalchemy.types import (
    Integer, String, Boolean,
    Unicode, DateTime, Float,
    Date,
)

from codecarrotsregistration import db


class User(db.Model, UserMixin):
    """
    User model for reviewers.
    """
    __tablename__ = 'user'
    id = Column(Integer, autoincrement=True, primary_key=True)
    active = Column(Boolean, default=True)
    email = Column(String(200))
    password = Column(String(200), default='')
    username = Column(String(200), unique=True)
    admin = Column(Boolean, default=False)
    poweruser = Column(Boolean, default=False)  # can accept attendees

    def is_poweruser(self):
        """
        Returns if user is active.
        """
        return self.poweruser

    def is_active(self):
        """
        Returns if user is active.
        """
        return self.active

    def is_admin(self):
        """
        Returns if user is admin.
        """
        return self.admin


class Attendee(db.Model):
    """
    Attendee Model.
    """
    __tablename__ = 'attendee'
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(50))
    surname = Column(Unicode(50))
    email = Column(String(80), unique=True)
    birth_date = Column(DateTime)
    description = Column(String(1000))
    app_idea = Column(String(1000))
    accepted_rules = Column(Boolean)
    can_cook_something = Column(String(50))
    city = Column(String(50))
    experience = Column(String(150))
    tshirt = Column(String(50))
    operating_system = Column(String(50))

    # meta data
    create_date = Column(DateTime, default=datetime.utcnow)
    score = Column(Float, default=0)
    reviewed_by = Column(String(500))
    accepted = Column(Boolean, default=False)
    notes = Column(String(5000))
    ssh_tag = Column(String(500))
    confirmation = Column(String(10), default='noans')
