#!/usr/bin/env python
# encoding: utf-8
from __future__ import unicode_literals
import json
import random
import hashlib

from codecarrotsregistration import app, db, mail, bcrypt, lm

from flask import redirect, render_template, request, flash, url_for
from flask.ext.login import login_required
from flask.ext.login import current_user
from flask.ext.mail import Message
from flask.ext.login import login_user
from forms import RegisterForm, LoginForm, ReviewForm, AMailForm
from models import Attendee, User
from wtforms import validators


def server_url():
    """
    Returns current server url.
    """
    url = str(request.url_root).rstrip('/')
    return url

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
            validators.EqualTo(i * i + i, message='Podałaś/eś błędny wynik')
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
            user = User.query.filter_by(
                username=request.form['username']).first()
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
        attendees = Attendee.query.order_by(Attendee.score.desc()).limit(
            100).all()
        current_page_id = 'overview_top100'
    elif user_filter == 'accepted':
        attendees = Attendee.query.filter(
            Attendee.accepted
        ).order_by(Attendee.surname.asc()).all()
        current_page_id = 'overview_accepted'
    elif user_filter == 'confirmed':
        attendees = Attendee.query.filter(
            Attendee.confirmation == 'yes'
        ).order_by(Attendee.surname.asc()).all()
        current_page_id = 'overview_confirmed'
    elif user_filter == 'unconfirmed':
        attendees = Attendee.query.filter(
            Attendee.confirmation == 'no'
        ).order_by(Attendee.surname.asc()).all()
        current_page_id = 'overview_unconfirmed'
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
        attendee.experience = json.dumps(attendee.experience)
        attendee.notes = request.form['notes']
        score = float(request.form['score'])
        if reviewed_by:
            reviewed_by[current_user.username] = score
            attendee.score = (attendee.score + score) / 2
        else:
            reviewed_by = {current_user.username: score}
        attendee.score = sum(reviewed_by.values()) / len(reviewed_by)
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
        if receivers == 'accepted':
            attendees = Attendee.query.filter(
                Attendee.accepted
            ).all()
        elif receivers == 'unaccepted':
            attendees = Attendee.query.filter(
                Attendee.accepted == False
            ).all()
        elif receivers == 'confirmed':
            attendees = Attendee.query.filter(
                Attendee.confirmation == 'yes'
            ).all()
        elif receivers == 'unconfirmed':
            attendees = Attendee.query.filter(
                Attendee.confirmation == 'noans'
            ).all()
        elif receivers == 'rejected':
            attendees = Attendee.query.filter(
                Attendee.confirmation == 'no'
            ).all()
        else:
            attendees = Attendee.query.all()
        count_mails = 0
        with mail.connect() as conn:
            for user in attendees:
                count_mails += 1
                msg = Message(recipients=[user.email],
                              body=body,
                              subject=subject)
                conn.send(msg)
        flash("You succesfully send {} e-mail to all {} attendees".format(
            count_mails, receivers
        ))
    return render_template('amail.html', form=form)


@app.route('/confirmation/<string:answer>/<string:ctag>', methods=['GET'])
def confirmation(answer, ctag):
    attendee = Attendee.query.filter(
        Attendee.ssh_tag == ctag
    ).first()
    if not attendee:
        flash('You have alredy answered or there is no user with that hash')
    attendee.ssh_tag = ""
    if answer == 'yes':
        attendee.confirmation = 'yes'
        message = "Yey ! Do zobaczenia 27meg Listopada"
    elif answer == 'no':
        attendee.confirmation = 'no'
        message = "Dzięki za opodiwedź szkoda że jednak nie możesz dołączyć :("
    else:
        message = 'Coś poszło nie tak!'
    flash(message)
    db.session.commit()
    return render_template('info.html')


@app.route('/send_confirmation', methods=['GET'])
@login_required
def send_confirmation():
    if not current_user.poweruser:
        return redirect('overview')
    attendees = Attendee.query.filter(
        Attendee.accepted
    ).all()
    count_mails = 0
    with mail.connect() as conn:
        for user in attendees:
            thash = hashlib.sha224(user.email).hexdigest()
            user.ssh_tag = thash
            yes_url = "{}{}".format(
                server_url(),
                url_for('confirmation', answer='yes', ctag=thash)
            )
            no_url = "{}{}".format(
                server_url(),
                url_for('confirmation', answer='no', ctag=thash)
            )
            subject = "Zostałaś wybrana na warsztaty PyCode Carrots w Poznaniu"
            body = """Gratluajcę !!! \n \n
                   Zostałaś wybrana na warsztaty PyCode Carrots w Poznaniu! \n\n
                   Potwierdź proszę swoją decyzję klikając w ten link: \n\n
                   ! UWAGA ! nie ma możliwości zmiany decyzji więc klikaj w przemyślany sposób:
                   \n\n{}\n\n
                   jeśli coś się zmieniło i nie możesz dotrzeć kliknij prosze w ten link:
                   \n\n{}\n\n
                   """.format(yes_url, no_url)
            count_mails += 1
            msg = Message(recipients=[user.email],
                          body=body,
                          subject=subject)
            conn.send(msg)
    db.session.commit()
    flash("You succesfully send {} e-mail to all accepted attendees".format(
        count_mails
    ))
    return redirect('overview')