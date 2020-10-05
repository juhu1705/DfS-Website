import functools
import os

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from dfs import home, util
from dfs.database import get_db
from dfs.emails import send_confirmation_email
from dfs.home import get_filename
from dfs.util import random_uri_safe_string

bp = Blueprint('auth', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'webp'}


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':

        try:
            username = request.form['username']
            password = request.form['password']
        except:
            flash('Post incorrect!')
            print('Post incorrect!')
            return redirect(url_for('home.index'))
        db = get_db()
        error = None

        user = db.execute('SELECT * FROM user WHERE name = ? OR email = ?', (username, username,)).fetchone()

        if user is None:
            error = 'Der Benutzername existiert nicht.'
        elif not check_password_hash(user['pwd_hash'], password):
            error = 'Das Passwort war falsch.'
        elif user['email_confirmed'] == 0:
            error = 'Ihre E-Mail ist noch nicht verifiziert.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']

            return redirect(url_for('home.index'))
        flash(error)

    return render_template('home/login.html')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            mail = request.form['mail']
            password = request.form['password']
            passwordcheck = request.form['passwordcheck']
            agreement = request.form['agreement']
        except:
            flash('Post incorrect!')
            flash('Unter umständen wurde der Datenschutzvereinbarung nicht zugestimmt! Diese Zustimmung ist erforderlich!')
            return redirect(url_for('home.index'))
        db = get_db()
        error = None
        user = db.execute('SELECT * FROM user WHERE name = ? or email = ?', (username, mail,)).fetchone()

        if not agreement:
            error = 'Es wurde der Datenschutzvereinbarung nicht zugestimmt!'
        elif user is not None:
            error = 'Der Benutzername oder die E-Mailaddresse sind bereits in Benutzung.'
        elif password != passwordcheck:
            error = 'Ihre Passwörter stimmen nicht überein.'
        elif not username:
            error = 'Sie haben keinen Benutzernamen angegeben.'
        elif not mail or not util.check_email(mail):
            error = 'Sie haben keine E-Mail Addresse angegeben.'

        if error is None:
            token = random_uri_safe_string(64)
            db.execute('INSERT INTO user (name, email, pwd_hash, level, email_confirmed, confirmation_token, visible)'
                       ' VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (username, mail, generate_password_hash(password), 0, 0, token, 0))
            db.commit()
            user = db.execute('SELECT * FROM user WHERE name = ? AND email = ?', (username, mail,)).fetchone()
            from dfs.emails import send_confirmation_email

            send_confirmation_email(user['email'], user, token)

            return redirect(url_for('auth.login'))
        flash(error)

    return render_template('home/register.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home.index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not g.user:
            flash('Du musst eingeloggt sein!')
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not g.user or g.user['level'] < getAdminKey():
            flash('Du benötigst Administratorberechtigungen!')
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


def writer_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not g.user or g.user['level'] < getWriterKey():
            flash('Diese Aktion bleibt dir verwehrt!')
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


def getAdminKey():
    return 2


def getWriterKey():
    return 1


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/reset', methods=('GET', 'POST'))
def reset_password():
    if request.method == 'POST':
        try:
            username = request.form['username']
            mail = request.form['mail']
        except:
            flash('Post incorrect!')
            return redirect(url_for('home.index'))

        db = get_db()
        user = db.execute('SELECT * FROM user WHERE name = ? AND email = ?', (username, mail)).fetchone()

        if user is not None:
            token = random_uri_safe_string(64)

            db.execute('UPDATE user SET password_reset_token = ? WHERE id = ?', (token, user['id'],))
            db.commit()
            from dfs.emails import send_password_reset_email

            send_password_reset_email(user['email'], user, token)
            return redirect(url_for('auth.login'))
    return render_template('home/reset_request.html')


@bp.route('/reset/<token>', methods=('GET', 'POST'))
def password_reset(token):
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE password_reset_token = ?', (token,)).fetchone()
    if user is not None:
        if request.method == 'POST':
            try:
                password = request.form['password']
                check = request.form['passwordcheck']
            except:
                flash('Post incorrect!')
                return redirect(url_for('home.index'))

            if password == check:
                db = get_db()
                db.execute('UPDATE user SET pwd_hash = ?, password_reset_token = ?',
                           (generate_password_hash(password), None,))
                db.commit()
                return redirect(url_for('auth.login'))
        return render_template('home/reset_password.html')
    else:
        return redirect(url_for('home.index'))


@bp.route('/confirm/<token>', methods=('GET', 'POST'))
def confirm_mail(token):
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE confirmation_token = ?', (token,)).fetchone()
    if user is not None:

        db = get_db()
        db.execute('UPDATE user SET email_confirmed = ?, confirmation_token = ?',
                   (1, None,))
        db.commit()

        return redirect(url_for('auth.login'))
    else:
        return redirect(url_for('home.index'))


@bp.route('/profile', methods=('GET', 'POST'))
@login_required
def profile():
    if request.method == 'POST':
        try:
            username = request.form['username']
            mail = request.form['mail']
            password = request.form['password']
        except:
            flash('Post incorrect!')
            print('Fehler')
            return redirect(url_for('home.index'))

        db = get_db()
        user = db.execute('SELECT * FROM user WHERE id=?', (g.user['id'],)).fetchone()
        check_user = db.execute('SELECT * FROM user WHERE (NOT id=?) and (name=? or email=?)',
                                (g.user['id'], username, mail)).fetchone()

        update = False
        error = None

        if user is None:
            error = 'Ihr Benutzerkonto existiert nicht mehr.'
        elif check_user is not None:
            error = 'Ein Benutzer mir diesem Namen existiert bereits, bitte wählen sie einen anderen Benutzernamen.'

        email_reset = False

        if error is None and user['email'] != mail:
            if util.check_email(mail):
                token = random_uri_safe_string(64)
                db.execute('UPDATE user SET email=?, email_confirmed = ?, confirmation_token = ? WHERE id = ?',
                           (mail, 0, token, g.user['id']))
                send_confirmation_email(mail, user, token)
                update = True
                email_reset = True
            else:
                flash('Es wurde keine E-Mail angegeben.')

        if error is None:
            if 'visible' in request.form:
                try:
                    visible = request.form['visible']
                except:
                    flash('Post incorrect!')
                    print('Fehler')
                    return redirect(url_for('home.index'))
                if visible == 'Sichtbar mit E-Mail':
                    db.execute('UPDATE user SET visible = ? WHERE id = ?', (2, g.user['id']))
                elif visible == 'Sichtbar ohne E-Mail':
                    db.execute('UPDATE user SET visible = ? WHERE id = ?', (1, g.user['id']))
                elif visible == 'Unsichtbar':
                    db.execute('UPDATE user SET visible = ? WHERE id = ?', (0, g.user['id']))

            if 'about_you' in request.form:
                db.execute('UPDATE user SET about_you = ? WHERE id = ?', (request.form['about_you'], g.user['id']))
            update = True

        if error is None and user['name'] != username:
            db.execute('UPDATE user SET name=? WHERE id = ?', (username, g.user['id']))
            update = True

        if error is None and 'new_password' in request.form and 'new_password2' in request.form:
            new_password = request.form['new_password']
            new_password2 = request.form['new_password2']

            error = None
            user = db.execute('SELECT * FROM user WHERE id=?', (g.user['id'],)).fetchone()

            if user is None:
                error = 'Ihr Benutzerkonto existiert nicht mehr.'
            elif new_password != new_password2:
                error = 'Bitte überprüfen sie ihr neues Passwort.'
            elif not username:
                error = 'Sie haben keinen Benutzernamen angegeben!'
            elif not (check_password_hash(user['pwd_hash'], password)):
                error = 'Ihr Passwort war falsch.'
            elif not new_password:
                new_password = password

            if error is None:
                db.execute('UPDATE user SET pwd_hash = ? WHERE id = ?',
                           (generate_password_hash(new_password), g.user['id']))
                update = True
            else:
                flash(error)
        db.commit()
        if 'image_loader' in request.files:
            file = request.files['image_loader']

            if file.filename == '':
                if email_reset:
                    return redirect(url_for('auth.logout'))
                if update:
                    return redirect(url_for('home.index'))
                else:
                    return render_template('home/profile.html', picture_name=os.path.join(
                        os.path.join(current_app.instance_path, 'assets/pictures/profile'),
                        str(g.user['id'])))

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)

                path = os.path.join(current_app.instance_path, 'assets/pictures/profile', str(g.user['id']))

                if os.path.exists(path) and get_filename(g.user['id']) is not None:
                    os.remove(os.path.join(path, get_filename(g.user['id'])))

                os.makedirs(path, exist_ok=True)

                file.save(os.path.join(path, 'profile_picture.' + filename.rsplit('.')[1].lower()))
                update = True

        if email_reset:
            return redirect(url_for('auth.logout'))

        if update:
            return redirect(url_for('home.index'))
    return render_template('home/profile.html', picture_name=os.path.join(
        os.path.join(current_app.instance_path, 'assets/pictures/profile'),
        str(g.user['id'])))


@bp.route('/profile/delete', methods=('GET', 'POST'))
@login_required
def delete_user():
    id = g.user['id']

    db = get_db()

    db.execute('DELETE FROM discussion WHERE author = ?', (id,))
    db.execute('DELETE FROM comment WHERE author = ?', (id,))
    db.execute('DELETE FROM short_stories WHERE author = ?', (id,))
    db.execute('DELETE FROM user_permissions WHERE user_id = ?', (id,))
    db.execute('DELETE FROM time_event WHERE author = ?', (id,))
    db.execute('DELETE FROM user WHERE id = ?', (id,))
    db.commit()

    path = os.path.join(current_app.instance_path, 'assets/pictures/profile', str(id), get_filename(id))

    if os.path.exists(path):
        path_extended = os.path.join(current_app.instance_path, os.path.join('assets/pictures/profile', str(id),
                                                                             get_filename(id)))
        print(path_extended)
        os.remove(path_extended)

    return redirect(url_for('auth.logout'))


@bp.route('/profile_picture')
@login_required
def profile_picture():
    return home.profile_picture(g.user['id'])


@bp.route('/profile/<int:id>/set-role/<int:status>')
@admin_required
def set_status(id, status):
    db = get_db()

    user = db.execute('SELECT * FROM user WHERE id = ?', (id,)).fetchone()
    if not user:
        abort(400)
        return

    db.execute('UPDATE user SET level=? WHERE id=?', (status, id))
    db.commit()

    return redirect(url_for('home.visit_profile', id=id))
