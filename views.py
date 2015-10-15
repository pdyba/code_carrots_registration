#!/usr/bin/env python
# encoding: utf-8
from __future__ import unicode_literals
import json
import random

from codecarrotsregistration import app, db, mail, bcrypt, lm

from flask import redirect, render_template, request, flash, url_for
from flask.ext.login import login_required
from flask.ext.login import current_user
from flask.ext.mail import Message
from flask.ext.login import login_user
from forms import RegisterForm, LoginForm, ReviewForm, AMailForm
from models import Attendee, User
from wtforms import validators


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    languages = [
        'Python', 'Ruby', 'C++',
        'Java', 'JavaScript', 'HTML/CSS',
        'Inny',
    ]
    for lan in languages:
        form.exp.append_entry(data={'name': lan})
    i = random.randint(2, 5)
    if request.method == 'GET':
        form.i_am_human.label = ('{} + {} * {} = ?'.format(i, i, i))
        form.i_am_human.validators = [
            validators.EqualTo(i*i+i, message='Podałaś/eś błędny wynik')
        ]
    if request.method == 'POST' and form.validate():
        new_attende = Attendee()
        form.populate_obj(new_attende)
        experience = {
            lan: request.form[lan] for lan in languages
        }
        new_attende.experience = json.dumps(experience)
        db.session.add(new_attende)
        db.session.commit()
        msg = Message(
            'PyCode Carrots Poznań 1. Registration Confirmation',
            recipients=[request.form.get('email')],
            body="Congrats You successfully registered"
                 "Good luck !"
                 "Poznań Carrot Team :D",
        )
        mail.send(msg)
        flash(
            'Congrats You successfully registered,'
            'You should receive e-mail confirmation'
        )
        return redirect(url_for('register'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST':
        if form.validate():
            user = User.query.filter_by(username=request.form['username']).first()
            if user is not None and bcrypt.check_password_hash(
                user.password, request.form['password']
            ):
                login_user(user)
                flash('You were logged in. Go Crazy.')
                return redirect(url_for('overview'))
            else:
                flash('Invalid username or password.')
    return render_template('login.html', form=form)


@app.route('/overview', methods=['GET', 'POST'])
@app.route('/overview/<string:user_filter>', methods=['GET', 'POST'])
@login_required
def overview(user_filter=None):
    if user_filter == 'notrated':
        attendees = Attendee.query.filter(
            Attendee.score == 0
        ).order_by(Attendee.surname.asc()).all()
        current_page_id = 'overview'
    elif user_filter == 'top100':
        attendees = Attendee.query.order_by(Attendee.score.desc()).limit(100).all()
        current_page_id = 'overview_top100'
    elif user_filter == 'accepted':
        attendees = Attendee.query.filter(
            Attendee.accepted
        ).order_by(Attendee.surname.asc()).all()
        current_page_id = 'overview_accepted'
    else:
        attendees = Attendee.query.all()
        current_page_id = 'overview_all'
    count = len(attendees)
    return render_template(
        'overview.html',
        attendees=attendees,
        count=count,
        current_page_id=current_page_id,
    )


@app.route('/review/<int:uid>', methods=['GET', 'POST'])
@login_required
def review(uid):
    form = ReviewForm(request.form)
    attendee = Attendee.query.get(uid)
    if attendee.reviewed_by:
        reviewed_by = json.loads(attendee.reviewed_by)
        form.notes.data = attendee.notes
    else:
        reviewed_by = None
    if not current_user.is_poweruser():
        del form.accepted
    if reviewed_by and current_user.username in reviewed_by:
        form.score.data = reviewed_by[current_user.username]
    attendee.experience = json.loads(attendee.experience)
    if request.method == 'POST':
        attendee.notes = request.form['notes']
        score = float(request.form['score'])
        if reviewed_by:
            reviewed_by[current_user.username] = score
            attendee.score = (attendee.score + score)/2
        else:
            reviewed_by = {current_user.username: score}
        attendee.score = sum(reviewed_by.values())/len(reviewed_by)
        attendee.reviewed_by = json.dumps(reviewed_by)
        if current_user.is_poweruser():
            attendee.accepted = request.form.get('accepted') == 'y'
        db.session.commit()
        flash('Review saved')
        return redirect(url_for('overview'))
    return render_template(
        'review.html',
        form=form,
        attendee=attendee,
        reviewed_by=reviewed_by,
    )


@app.route('/', methods=['GET', 'POST'])
def info():
    return render_template('info.html')


@app.route('/amail', methods=['GET', 'POST'])
@login_required
def amail():
    form = AMailForm(request.form)
    if request.method == 'POST' and form.validate():
        subject = request.form.get('subject')
        body = request.form.get('body')
        receivers = request.form.get('receivers')
        receivers_list = []
        msg = Message(
            subject,
            recipients=receivers_list,
            body=body,
        )
        mail.send(msg)
    return render_template('amail.html', form=form)