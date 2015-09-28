__author__ = 'Piotr Dyba'

import json

from codecarrotsregistration import app, db, mail, bcrypt, lm

from flask import redirect, render_template, request, flash, url_for, jsonify
from flask.ext import login
from flask.ext.login import current_user
from flask.ext.mail import Message
from sqlalchemy.orm import load_only
from flask.ext.login import login_user
from forms import RegisterForm, LoginForm, ReviewForm
from models import Attendee, User


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST':
        new_attende = Attendee()
        form.populate_obj(new_attende)
        db.session.add(new_attende)
        db.session.commit()
        flash(
            'Congrats You succesfuly registered,'
            'You should recive e-mail confirmation'
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
def overview(user_filter=None):
    if user_filter == 'notrated':
        attendees = Attendee.query.filter(
            Attendee.score == 0
        ).order_by(Attendee.surname.asc()).all()
    elif user_filter == 'top100':
        attendees = Attendee.query.order_by(Attendee.score.desc()).limit(100).all()
    elif user_filter == 'accepted':
        attendees = Attendee.query.filter(
            Attendee.accepted
        ).order_by(Attendee.surname.asc()).all()
    else:
        attendees = Attendee.query.all()
    count = len(attendees)
    return render_template(
        'overview.html',
        attendees=attendees,
        count=count,
    )


@app.route('/review/<int:uid>', methods=['GET', 'POST'])
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
    if request.method == 'POST':
        attendee.notes = request.form['notes']
        score = int(request.form['score'])
        if reviewed_by:
            reviewed_by[current_user.username] = score
            attendee.score = (attendee.score + score)/2
        else:
            reviewed_by = {current_user.username: score}
        attendee.score = sum(reviewed_by.values())/len(reviewed_by)
        attendee.reviewed_by = json.dumps(reviewed_by)
        if current_user.is_poweruser():
            attendee.accepted = request.form['accepted'] == 'y'
        db.session.commit()
        flash('Review saved')
        return redirect(url_for('overview'))
    return render_template(
        'review.html',
        form=form,
        attendee=attendee,
        reviewed_by=reviewed_by,
    )


@app.route('/info', methods=['GET', 'POST'])
def info():
    return render_template('info.html')
