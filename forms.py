__author__ = 'Piotr Dyba'

from wtforms import (
    Form,
    validators,
    TextAreaField,
    IntegerField,
    BooleanField,
    SelectField,
    DateField,
    FloatField,
    StringField,
    SelectMultipleField,
    PasswordField,
)


class RegisterForm(Form):
    """
    Attendee registration Form
    """
    name = StringField(
        "name",
        validators=[validators.DataRequired('Please enter your name.')],
    )
    surname = StringField(
        "surname",
        validators=[validators.DataRequired('Please enter your surname.')],
    )
    email = StringField(
        "email",
        validators=[validators.DataRequired('Please enter your email.')],
    )
    birth_date = DateField(
        label='birth_date',
        format="%Y-%m-%d",
    )
    description = TextAreaField(
        "description",
        validators=[validators.DataRequired('Please enter your description.')],
    )
    accepted_rules = BooleanField(
        "accepted_rules",
        validators=[validators.DataRequired('Please accept rules.')],
    )
    riddle = TextAreaField(
        "description",
        validators=[validators.DataRequired('Please enter your description.')],
    )
    can_cook_something = SelectField(
        'can_cook_something',
        validators=[validators.DataRequired("Please choose if you can cook")],
        choices=[
            ('cake', 'I can cook some cake, snack'),
            ('sandwitch', 'I cane prepare sandwitches'),
            ('no', 'Sorry I cannot cook'),
        ]
    )
    i_am_human = IntegerField(
        'i_am_human',
        validators=[validators.DataRequired("Please choose if you can cook")],
    )
    city = StringField(
        "city",
        validators=[validators.DataRequired('Please enter your city.')],
    )


class ReviewForm(Form):
    """
    Attendee registration Form
    """
    score = SelectField(
        'score',
        validators=[validators.DataRequired("Please choose a score")],
        choices=[
            (1, 1),
            (2, 2),
            (3, 3),
            (4, 4),
            (5, 5),
            (6, 6),
            (7, 7),
            (8, 8),
            (9, 9),
            (10, 10),
        ]
    )
    notes = TextAreaField(
        "notes",
        validators=[validators.DataRequired('Please enter your description.')],
    )
    accepted = BooleanField(
        'accepted',
    )


class LoginForm(Form):
    username = StringField(
        "description",
        validators=[validators.DataRequired('Please enter your name.')],
    )
    password = PasswordField(
        "description",
        validators=[validators.DataRequired('Please enter your name.')],
    )
