#!/usr/bin/env python
# encoding: utf-8
from __future__ import unicode_literals

from datetime import date
import random

from wtforms import (
    Form,
    validators,
    TextAreaField,
    IntegerField,
    BooleanField,
    SelectField,
    DateField,
    StringField,
    RadioField,
    PasswordField,
    FieldList,
    Label,
)
from wtforms_html5 import DateRange


class MyFieldList(FieldList):
    def _add_entry(self, data=None):
        field = super(MyFieldList, self)._add_entry(data=data)
        name = data.get('name')
        if name:
            field.name = name
            field.label = Label(name.lower(), name)
            field.default = ('0', 'Nie znam')
        return field

    def append_entry(self, data=None):
        return self._add_entry(data=data)


class RegisterForm(Form):
    """
    Attendee registration Form
    """
    name = StringField(
        "name",
        validators=[
            validators.DataRequired('Podaj swoje imię.'),
            validators.Length(
                min=2, max=30,
                message='Podałeś nie istniejące imie.'
            )

        ],
    )
    surname = StringField(
        "surname",
        validators=[
            validators.DataRequired('Podaj swoje nazwisko.'),
            validators.Length(
                min=2, max=50,
                message='Podałeś nie istniejące nazwisko.'
            )
        ],
    )
    email = StringField(
        "email",
        validators=[validators.Email('Podaj swój e-mail.')],
    )
    birth_date = DateField(
        label='birth_date',
        format="%Y-%m-%d",
        validators=[
            validators.DataRequired('Podaj swoją datę urodzenia.'),
            DateRange(
                min=date(1900, 1, 1),
                max=date(1997, 12, 30)
            ),
        ],
    )
    telephone = StringField(
        'telephone',
        validators=[
            validators.DataRequired("Podaj swój numer telefonu")
        ],
    )
    description = TextAreaField(
        "description",
        validators=[
            validators.DataRequired(
                'Napisz co Cię motywuję do rozpoczęcia przygody z programowaniem'
            ),
            validators.Length(
                min=100,
                max=550,
                message="""Napisałeś zbyt opis swojej motywacji
                skróc go do 500 znaków """
            ),
        ],
    )
    app_idea = TextAreaField(
        "app_idea",
        validators=[
            validators.DataRequired('Napisz swój pomysł na aplikację.'),
            validators.Length(
                min=20,
                max=250,
                message="""Napisałeś zbyt długi pomysł na
                aplikacje - skróc go do 200 znaków """
            ),
        ],
    )
    accepted_rules = BooleanField(
        "accepted_rules",
        validators=[validators.DataRequired('Musisz zakceptować regulamin')],
    )
    can_cook_something = SelectField(
        'can_cook_something',
        validators=[validators.DataRequired("Daj znać czy umiesz gotować")],
        choices=[
            ('Upiekę coś słodkiego',)*2,
            ('Przygtuje kanapki, coś nie słodkiego',)*2,
            ('Wezmę ze sobą jakieś przekąski',)*2,
            ('Niestety nie mogę nic przygotować',)*2,
            ('Inne', 'Inne'),
        ]
    )
    operating_system = SelectField(
        'operating_system',
        validators=[validators.DataRequired("Wybierz system operacyjny")],
        choices=[
            ('macos', 'MacOS'),
            ('linux', 'Linux'),
            ('windows', 'Windows'),
        ]
    )

    exp = MyFieldList(RadioField(
        validators=[validators.optional()],
        choices=[
            ('0', 'Nie znam'),
            ('1', 'Początkujący'),
            ('2', 'Średniozaawansowany'),
            ('3', 'Zaawansowany'),
        ]),
    )

    tshirt = SelectField(
        'tshirt',
        validators=[validators.DataRequired("Wybierz rozmiar koszulki")],
        choices=[
            ("{} {}".format(sex, size),)*2 for sex in
            ['Damska', 'Męska'] for size in ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        ]
    )

    i_am_human = IntegerField(
        'i_am_human',
        validators=[validators.AnyOf(
            [6, 12, 20, 30],
            message='Podałaś/eś błędny wynik weryfikacji'
        )]
    )

    city = StringField(
        "city",
        validators=[validators.DataRequired('Podaj swoje miasto.')],
    )


class ReviewForm(Form):
    """
    Attendee registration Form
    """
    score = SelectField(
        'score',
        validators=[validators.DataRequired("Please choose a score")],
        choices=[(i, i) for i in range(1, 11)]
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


class AMailForm(Form):
    receivers = SelectField(
        'receivers',
        validators=[validators.DataRequired("Wybierz grupe docelową")],
        choices=[
            ('all',)*2,
            ('accepted',)*2,
            ('unaccepted',)*2,
            ('confirmed',)*2,
            ('unconfirmed',)*2,
            ('rejected',)*2,
        ]
    )
    subject = StringField(
        "subject",
        validators=[validators.DataRequired('Podaj temat')],
    )
    body = TextAreaField(
        "body",
        validators=[validators.DataRequired('Napisz Treść maila')],
    )