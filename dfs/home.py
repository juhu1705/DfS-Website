import functools, os

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app, send_from_directory,
    send_file
)
from werkzeug.security import check_password_hash, generate_password_hash

from dfs.database import get_db

bp = Blueprint('home', __name__)


@bp.route('/')
def index():
    db = get_db()
    discussions = db.execute('SELECT * FROM discussion d, user u WHERE d.author = u.id ORDER BY d.created DESC').fetchmany(3)
    comments = db.execute('SELECT d.id AS id, COUNT(c.id) AS comments '
                          'FROM comment c, discussion d '
                          'WHERE d.id = c.discussion_id '
                          'GROUP BY d.id').fetchall()

    return render_template('home/home.html', discussions=discussions, comments=comments, i=0)


@bp.route('/profiles', methods=('GET', 'POST'))
def profiles():
    db = get_db()
    users = db.execute('SELECT * FROM user WHERE visible = 1').fetchall()

    return render_template('home/accounts.html', users=users)


@bp.route('/profile/<int:id>', methods=('GET', 'POST'))
def visit_profile(id):
    user = get_db().execute('SELECT * FROM user WHERE id = ?', (id, )).fetchone()
    if(user['visible']):
        discussions = get_db().execute('SELECT * FROM discussion d, user u WHERE d.author = ? AND d.author = u.id', (id, )).fetchall()
        short_stories = get_db().execute('SELECT * FROM short_stories s, user u WHERE s.author = ?  AND s.author = u.id', (id,)).fetchall()
        time_events = get_db().execute('SELECT * FROM time_event t, user u WHERE t.author = ? AND t.author = u.id', (id,)).fetchall()
        characters = get_db().execute('SELECT c.name, c.family, c.id FROM user_permissions up, user u, characters c'
                                      ' WHERE up.user_id = ? AND up.user_id = u.id AND up.character_id = c.id', (id,)).fetchall()

        print(characters)

        return render_template('home/account.html', user=user, discussions=discussions, short_stories=short_stories,
                               time_events=time_events, characters=characters)
    else:
        return redirect(url_for('home.profiles'))


@bp.route('/profile_picture/<int:id>')
def profile_picture(id):
    path = os.path.join(current_app.instance_path, 'assets\\pictures\\profile', str(id), get_filename(id))

    if os.path.exists(path):
        path_extended = os.path.join(current_app.instance_path, os.path.join('assets\\pictures\\profile', str(id),
                                                                             get_filename(id)))
        print(path_extended)
        return send_file(path_extended)
    else:
        return send_from_directory('static', 'pictures/blank.png')


def get_filename(id: int):
    if os.path.exists(os.path.join(current_app.instance_path, 'assets\\pictures\\profile', str(id))):
        for file in os.listdir(os.path.join(current_app.instance_path, 'assets\\pictures\\profile', str(id))):
            if file.startswith("profile_picture."):
                return file
    else:
        return 'profile_picture'


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not g.user or g.user['level'] < 2:
            flash('Du benötigst Administratorberechtigungen!')
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


@bp.route('/profile/<int:id>/delete', methods=('GET', 'POST'))
@admin_required
def delete_user(id):
    db = get_db()

    db.execute('DELETE FROM discussion WHERE author = ?', (id, ))
    db.execute('DELETE FROM comment WHERE author = ?', (id,))
    db.execute('DELETE FROM short_stories WHERE author = ?', (id,))
    db.execute('DELETE FROM user_permissions WHERE user_id = ?', (id,))
    db.execute('DELETE FROM time_event WHERE author = ?', (id,))
    db.execute('DELETE FROM user WHERE id = ?', (id,))
    db.commit()

    return redirect(url_for('home.profiles'))



