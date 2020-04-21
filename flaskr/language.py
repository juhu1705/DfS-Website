import functools
import os

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app, send_from_directory,
    send_file)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from flaskr import home
from flaskr.database import get_db
from flaskr.emails import send_confirmation_email
from flaskr.home import profile_picture, get_filename
from flaskr.auth import login_required, writer_required, admin_required
from flaskr.util import random_uri_safe_string

bp = Blueprint('language', __name__, url_prefix='/language')


@bp.route('/')
def index():
    db = get_db()

    languages = db.execute('SELECT * FROM language ORDER BY name ASC').fetchall()

    return render_template('language/languages.html', languages=languages)


@bp.route('/<int:id>')
def language(id):
    db = get_db()

    language = db.execute('SELECT * FROM language WHERE id = ?', (id, )).fetchone()
    words = db.execute('SELECT * FROM word WHERE language_id = ?', (id, )).fetchall()

    return render_template('language/language.html', language=language, words=words)


@bp.route('/create', methods=('GET', 'POST'))
@admin_required
def create_language():
    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form['description']
        except:
            flash('Deine mitgegebenen Daten konnten nicht gefunden werden. Bitte versuche es noch einmal.')
            return render_template('language/create_language.html')

        if not name or not description:
            flash('Sie haben nicht alle benötigten Werte angegeben!')
            return render_template('language/create_language.html')

        db = get_db()

        language = db.execute('SELECT * FROM language WHERE name = ?', (name, )).fetchone()

        if language is not None:
            flash('Diese Sprache existiert bereits.')
            return render_template('language/create_language.html')

        db.execute('INSERT INTO language (name, description) VALUES (?, ?)', (name, description))
        db.commit()

        return redirect(url_for('language.index'))
    return render_template('language/create_language.html')


@bp.route('/<int:id>/edit', methods=('GET', 'POST'))
@admin_required
def edit_language(id):
    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form['description']
            writing = request.form['select_writing']
        except:
            flash('Deine mitgegebenen Daten konnten nicht gefunden werden. Bitte versuche es noch einmal.')
            return render_template('language/create_language.html')

        if not name or not description:
            flash('Sie haben nicht alle benötigten Werte angegeben!')
            return render_template('language/create_language.html')

        db = get_db()

        language = db.execute('SELECT * FROM language WHERE id = ?', (id, )).fetchone()

        if language is None:
            flash('Diese Sprache existiert noch nicht. Du musst sie zunächst erstellen')
            return render_template('language/create_language.html')

        if language['name'] != name:
            name_check = db.execute('SELECT * FROM language WHERE name = ?', (name, )).fetchone()
            if name_check is not None:
                flash('Diese Sprache existiert bereits. Wähle einen anderen Namen!')
                return render_template('language/create_language.html')
            db.execute('UPDATE language SET name = ? WHERE id = ?', (name, id))

        if language['description'] != description:
            db.execute('UPDATE language SET description = ? WHERE id = ?', (description, id))


        db.execute('INSERT INTO language (name, description) VALUES (?, ?)', (name, description))
        db.commit()

        return redirect(url_for('language.index'))


    db = get_db()

    language = db.execute('SELECT * FROM language WHERE id = ?', (id, )).fetchone()
    writing = db.execute('SELECT * FROM writing').fetchall()

    return render_template('language/edit_language.html', language=language, writing=writing)


@bp.route('/<int:id>/create_word', methods=('GET', 'POST'))
@admin_required
def create_word_category(id):
    return render_template('')


@bp.route('/<int:id>/create_word', methods=('GET', 'POST'))
@admin_required
def create_word(id):
    if request.method == 'POST':
        try:
            word = request.form['word']
            translation = request.form['translation']
            description = request.form['description']
            word_category = request.form['word_category']
        except:
            flash('Deine mitgegebenen Daten konnten nicht gefunden werden. Bitte versuche es noch einmal.')
            return render_template('language/create_language.html')

        if not translation or not word or not word_category:
            flash('Sie haben nicht alle benötigten Werte angegeben!')
            return render_template('language/create_language.html')

        if not description:
            description = ''

        db = get_db()

        word_category_check = db.execute('SELECT * FROM word_category WHERE name = ?', (word_category,)).fetchone()

        if word_category_check is None:
            flash('Diese Wortart existiert nicht!')
            return render_template('language/create_word.html')

        word_check = db.execute('SELECT * FROM word WHERE word = ? AND translation = ?'
                                ' AND language_id = ? AND word_category_id = ?',
                                (word, translation, id, word_category_check['id'])).fetchone()

        if word_check is not None:
            flash('Dieses Wort existiert bereits.')
            return render_template('language/create_word.html')

        db.execute('INSERT INTO language (word, translation, description, word_category_id, language_id)'
                   ' VALUES (?, ?, ?, ?, ?)', (word, translation, description, word_category_check['id'], id))
        db.commit()

        return redirect(url_for('language.language', id=id))
    return render_template('language/create_word.html')
