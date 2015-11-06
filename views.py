#!/usr/bin/env python
# encoding: utf-8
from __future__ import unicode_literals
import json
import random
import hashlib
from sqlalchemy import and_

from codecarrotsregistration import app, db, mail, bcrypt, lm

from flask import redirect, render_template, request, flash, url_for
from flask.ext.login import login_required, logout_user
from flask.ext.login import current_user
from flask.ext.mail import Message
from flask.ext.login import login_user
from forms import RegisterForm, LoginForm, ReviewForm, AMailForm
from models import Attendee, User, Settings, MailHistory


def server_url():
    """
    Returns current server url.
    """
    url = str(request.url_root).rstrip('/')
    return url

EMAIL_CONFIRMATION = '''
Cześć!<br>
Dziękujemy za rejestrację na warsztaty PyCode Carrots w Poznaniu. Do 15 listopada otrzymasz informację o statusie Twojego zgłoszenia.<br>
<br>
Obserwuj nasze <a href='https://www.facebook.com/events/817378328361206/'>wydarzenie na Facebooku</a>!<br>
<br>
Pozdrawiamy,<br>
Carrots Team
'''
EMAIL_ACCEPTED = '''
Cześć!<br>
Z przyjemnością informujemy, że Twoje zgłoszenie na warsztaty PyCode Carrots w Poznaniu zostało zaakceptowane. Przypominamy, że wydarzenie odbędzie się w dniach 27-29 listopada 2015 r. na Wydziale Matematyki i Informatyki UAM (ul. Umultowska 87).<br>
<br>
Żeby wziąć udział w warsztatach musisz kliknąć w link poniżej lub skopiować go i wkleić w pasek przeglądarki (link jest jednorazowego użycia).<br>
 <br>
UWAGA TEJ OPERACJI NIE MOŻNA COFNĄĆ !<br>
<a href="{yes}">{yes}</a><br>
<br>
Jeśli jednak nie możesz dotrzeć kliknij proszę lub skopiuj link poniżej:<br>
<br>
UWAGA TEJ OPERACJI NIE MOŻNA COFNĄĆ !<br>
<a href="{no}">{no}</a><br>
<br>
Czekamy do środy 18 listopada (godz. 23:59) na potwierdzenie Twojego uczestnictwa w warsztacie. W przypadku braku odpowiedzi - na Twoje miejsce przydzielimy osobę z listy rezerwowej. Jeśli wiesz, że nie możesz skorzystać z warsztatu, również prosimy o informację zwrotną.<br>
<br>
Obserwuj nasze <a href='https://www.facebook.com/events/817378328361206/'>wydarzenie na Facebooku</a>!<br>
<br>
Pozdrawiamy,<br>
Carrots Team<br>
'''


def is_registration_active():
    return Settings.query.get(1).registration_status == 'active'


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if not is_registration_active():
        flash("Rejestracja już się skończyła dziękujemy za zaintersowania!")
        return redirect('/')
    form = RegisterForm(request.form)
    languages = [
        'Python', 'Ruby', 'C++',
        'Java', 'JavaScript', 'HTML/CSS',
        'Inny',
    ]
    i = random.randint(2, 5)
    text = '{} + {} * {} = ?'.format(i, i, i)
    form.i_am_human.label = text
    for lan in languages:
        form.exp.append_entry(data={'name': lan})
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
            'Potwierdzenie rejestracji na warsztaty PyCode Carrots Poznań',
            recipients=[request.form.get('email')],
            html=EMAIL_CONFIRMATION
        )
        mail.send(msg)
        flash(
            'Twoja odpowiedź została zapisana. '
            'Powinieneś dostać potwierdzenie na podany e-mail.'
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
                flash('Hi {}{} ! You were logged in. Go Crazy.'.format(
                    user.username[0].upper(), user.username[1:]
                ))
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
    for attendee in attendees:
        attendee.reviewed_by = len(json.loads(
            attendee.reviewed_by if attendee.reviewed_by else "{}"
        ))
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
        return redirect(url_for('overview', user_filter='notrated'))
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
        new_entry = MailHistory()
        new_entry.recivers = receivers
        new_entry.body = body
        new_entry.subject = subject
        new_entry.who_send = current_user.username
        db.session.add(new_entry)
        db.session.commit()
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
        flash('Już wykorzystałeś link lub podałeś błędny link')
    attendee.ssh_tag = ""
    if answer == 'yes':
        attendee.confirmation = 'yes'
        message = "Yey ! Do zobaczenia 27-meg listopada"
    elif answer == 'no':
        attendee.confirmation = 'no'
        message = '''
        Dziękujemy za odpowiedź. Szkoda, że jednak nie możesz dołączyć :(
        '''
    else:
        message = 'Coś poszło nie tak!'
    flash(message)
    db.session.commit()
    return render_template('info.html')


@app.route('/send_confirmation/<string:state>', methods=['GET'])
@login_required
def send_confirmation(state):
    global EMAIL_ACCEPTED
    if not current_user.poweruser:
        return redirect('overview')
    if state == 'rest':
        attendees = Attendee.query.filter(and_(
            Attendee.accepted,
            Attendee.confirmation == 'noans'
        )
        ).all()
        EMAIL_ACCEPTED = EMAIL_ACCEPTED.replace(
            'środy 18 listopada', 'niedzili 22 listopada'
        )
    else:
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
            subject = "PyCode Carrots Poznań: Wybraliśmy właśnie Ciebie"
            count_mails += 1
            msg = Message(
                recipients=[user.email],
                html=EMAIL_ACCEPTED.format(
                    **{'yes': yes_url, 'no': no_url}
                ),
                subject=subject
            )
            conn.send(msg)
    db.session.commit()
    flash("You succesfully send {} e-mail to all accepted attendees".format(
        count_mails
    ))
    return redirect('overview')


@app.route('/mailhistory', methods=['GET'])
@login_required
def mailhistory():
    if not current_user.is_admin():
        redirect('/')
    history = MailHistory.query.all()
    return render_template('mailhistory.html', history=history)


@app.route('/change_reg_status/<int:state>', methods=['GET'])
@login_required
def change_reg_status(state):
    if not current_user.poweruser:
        return redirect('overview')
    settings = Settings.query.get(1)
    if state == 0:
        settings.registration_status = 'finished'
        flash('Rejstracja wyłączona!')
    else:
        settings.registration_status = "active"
        flash('Rejstracja włączona!')
    db.session.commit()
    return redirect('overview')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/manage', methods=['GET'])
@login_required
def manage():
    if not current_user.is_poweruser():
        redirect('/')
    reg_stat = Settings.query.get(1).registration_status
    state = 'NIE AKTYWNA' if reg_stat == 'finished' else "AKTYWNA"
    return render_template('manage.html', state=state)


@app.route("/statistics")
@login_required
def statistics():
    data = {
        'all': Attendee.query.count(),
        'notrated': Attendee.query.filter(Attendee.score == 0).count()
    }
    return json.dumps(data)
