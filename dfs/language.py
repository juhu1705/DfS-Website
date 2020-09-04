import functools
import os

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app, send_from_directory,
    send_file)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from dfs import home
from dfs.database import get_db
from dfs.emails import send_confirmation_email
from dfs.home import profile_picture, get_filename
from dfs.auth import login_required, writer_required, admin_required
from dfs.util import random_uri_safe_string

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

    if language is None:
        flash('Diese Sprache existiert nicht!')
        return redirect(url_for('language.index'))

    words = db.execute('SELECT * FROM word WHERE language_id = ?', (id, )).fetchall()

    all_categories = db.execute('SELECT * FROM word_category ORDER BY name ASC').fetchall()

    categories = db.execute('SELECT wc.id, wc.name, wc.description'
                            ' FROM word_category wc, language_to_word_category ltwc'
                            ' WHERE ltwc.language_id = ? AND ltwc.word_category_id = wc.id'
                            ' ORDER BY wc.name ASC',
                            (id,)).fetchall()

    return render_template('language/language.html', language=language, words=words, categories=categories, all_categories=all_categories)


@bp.route('/create/language', methods=('GET', 'POST'))
@admin_required
def create_language():
    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form['description']
        except:
            flash('Deine mitgegebenen Daten konnten nicht gefunden werden. Bitte versuche es noch einmal.')
            return render_template('language/create.html', title='Sprache hinzufügen')

        if not name or not description:
            flash('Sie haben nicht alle benötigten Werte angegeben!')
            return render_template('language/create.html', title='Sprache hinzufügen')

        db = get_db()

        language = db.execute('SELECT * FROM language WHERE name = ?', (name, )).fetchone()

        if language is not None:
            flash('Diese Sprache existiert bereits.')
            return render_template('language/create.html', title='Sprache hinzufügen')

        db.execute('INSERT INTO language (name, description) VALUES (?, ?)', (name, description))
        db.commit()

        return redirect(url_for('language.index'))
    return render_template('language/create.html', title='Sprache hinzufügen')


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

        db.commit()

        return redirect(url_for('language.language', id=id))

    db = get_db()

    language = db.execute('SELECT * FROM language WHERE id = ?', (id, )).fetchone()
    writing = db.execute('SELECT * FROM writing').fetchall()

    return render_template('language/edit_language.html', language=language, writing=writing)


@bp.route('/<int:id>/delete', methods=('GET', 'POST'))
@admin_required
def delete_language(id):
    db = get_db()

    db.execute('DELETE FROM language WHERE id = ?', (id, ))
    db.execute('DELETE FROM word WHERE language_id = ?', (id, ))

    words = db.execute('SELECT * FROM word WHERE language_id = ?', (id, )).fetchall()
    for word in words:
        db.execute('DELETE FROM word_declinations WHERE parent_word_id = ?', (word['id'], ))

    db.execute('DELETE FROM word WHERE language_id = ?', (id, ))

    db.commit()

    return redirect(url_for('language.index'))


@bp.route('/<int:id>/add_category/<int:category_id>', methods=('GET', 'POST'))
@admin_required
def add_category_to_language(id, category_id):
    db = get_db()

    language = db.execute('SELECT * FROM language WHERE id = ?', (id, )).fetchone()
    category = db.execute('SELECT * FROM word_category WHERE id = ?', (category_id, )).fetchone()

    if language is not None and category is not None:
        if db.execute('SELECT * FROM language_to_word_category WHERE language_id = ? AND word_category_id = ?',
                      (id, category_id)).fetchone() is None:
            db.execute('INSERT INTO language_to_word_category (language_id, word_category_id) VALUES (?, ?)',
                       (id, category_id))
            db.commit()
        else:
            flash('Dieser Eintrag existiert bereits.')
    else:
        flash('Sprache oder Wortart existiert nicht!')

    return redirect(url_for('language.language', id=id))


@bp.route('/<int:id>/remove_category/<int:category_id>', methods=('GET', 'POST'))
@admin_required
def remove_category_from_language(id, category_id):
    db = get_db()

    language = db.execute('SELECT * FROM language WHERE id = ?', (id, )).fetchone()
    category = db.execute('SELECT * FROM word_category WHERE id = ?', (category_id, )).fetchone()

    if language is not None and category is not None:
        if db.execute('SELECT * FROM language_to_word_category WHERE language_id = ? AND word_category_id = ?',
                      (id, category_id)).fetchone() is not None:
            db.execute('DELETE FROM language_to_word_category WHERE language_id = ? AND word_category_id = ?',
                       (id, category_id))
            db.commit()
        else:
            flash('Dieser Eintrag existiert nicht!')
    else:
        flash('Sprache oder Wortart existiert nicht!')

    return redirect(url_for('language.language', id=id))


@bp.route('/<int:id>/create_word', methods=('GET', 'POST'))
@admin_required
def create_word(id):
    db = get_db()

    categories = db.execute('SELECT wc.id, wc.name, wc.description'
                            ' FROM word_category wc, language_to_word_category ltwc'
                            ' WHERE ltwc.language_id = ? AND ltwc.word_category_id = wc.id'
                            ' ORDER BY wc.name ASC',
                            (id, )).fetchall()

    if request.method == 'POST':
        try:
            word = request.form['word']
            translation = request.form['translation']
            description = request.form['description']
            word_category = request.form['word_category']
        except:
            flash('Deine mitgegebenen Daten konnten nicht gefunden werden. Bitte versuche es noch einmal.')
            return render_template('language/create_language.html', categories=categories)

        if not translation or not word or not word_category:
            flash('Sie haben nicht alle benötigten Werte angegeben!')
            return render_template('language/create_language.html', categories=categories)

        if not description:
            description = ''

        word_category_check = db.execute('SELECT * FROM word_category WHERE name = ?', (word_category,)).fetchone()

        if word_category_check is None:
            flash('Diese Wortart existiert nicht!')
            return render_template('language/create_word.html', categories=categories)

        word_check = db.execute('SELECT * FROM word WHERE word = ? AND translation = ?'
                                ' AND language_id = ? AND word_category_id = ?',
                                (word, translation, id, word_category_check['id'])).fetchone()

        if word_check is not None:
            flash('Dieses Wort existiert bereits.')
            return render_template('language/create_word.html', categories=categories)

        db.execute('INSERT INTO word (word, translation, description, word_category_id, language_id)'
                   ' VALUES (?, ?, ?, ?, ?)', (word, translation, description, word_category_check['id'], id))
        db.commit()

        return redirect(url_for('language.language', id=id))

    return render_template('language/create_word.html', categories=categories)


@bp.route('/create/category', methods=('GET', 'POST'))
@admin_required
def create_category():
    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form['description']
        except:
            flash('Deine mitgegebenen Daten konnten nicht gefunden werden. Bitte versuche es noch einmal.')
            return render_template('language/create.html', title='Wortart hinzufügen')

        if not name or not description:
            flash('Sie haben nicht alle benötigten Werte angegeben!')
            return render_template('language/create.html', title='Wortart hinzufügen')

        db = get_db()

        category = db.execute('SELECT * FROM word_category WHERE name = ?', (name, )).fetchone()

        if category is not None:
            flash('Diese Wortart existiert bereits.')
            return render_template('language/create.html', title='Wortart hinzufügen')

        db.execute('INSERT INTO word_category (name, description) VALUES (?, ?)', (name, description))
        db.commit()

        return redirect(url_for('language.categories'))
    return render_template('language/create.html', title='Wortart hinzufügen')


@bp.route('/category/<int:id>/edit', methods=('GET', 'POST'))
@admin_required
def edit_category(id):
    db = get_db()

    category = db.execute('SELECT * FROM word_category WHERE id = ?', (id, )).fetchone()

    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form['description']
        except:
            flash('Deine mitgegebenen Daten konnten nicht gefunden werden. Bitte versuche es noch einmal.')
            return render_template('language/create.html', title='Wortart hinzufügen')

        if not name or not description:
            flash('Sie haben nicht alle benötigten Werte angegeben!')
            return render_template('language/create.html', title='Wortart hinzufügen')

        db = get_db()

        category = db.execute('SELECT * FROM word_category WHERE name = ? AND id != ?', (name, id)).fetchone()

        if category is not None:
            flash('Diese Wortart existiert bereits.')
            return render_template('language/create.html', title='Wortart hinzufügen')

        db.execute('UPDATE word_category SET name = ?, description = ? WHERE id = ?', (name, description, id))
        db.commit()

        return redirect(url_for('language.categories'))
    return render_template('language/edit_category.html', title='Wortart bearbeiten', category=category)


@bp.route('/category/<int:id>/delete', methods=('GET', 'POST'))
@admin_required
def delete_category(id):
    db = get_db()

    words = db.execute('SELECT * FROM word WHERE word_category_id = ?', (id, )).fetchall()
    for word in words:
        db.execute('DELETE FROM word_declinations WHERE parent_word_id = ?', word['id'])

    db.execute('DELETE FROM word WHERE word_category_id = ?', (id, ))
    db.execute('DELETE FROM language_to_word_category WHERE word_category_id = ?', (id, ))

    declinations = db.execute('SELECT * FROM declination WHERE word_category_id = ?', (id,)).fetchall()
    for declination in declinations:
        declinated_words = db.execute('SELECT * FROM word_declinations WHERE declination_id = ?', (declination['id'], )).fetchall()
        for word in declinated_words:
            db.execute('DELETE FROM word WHERE id = ?', (word['parent_word_id'], ))
        db.execute('DELETE FROM word_declinations WHERE declination_id = ?', (declination['id'], ))

    db.execute('DELETE FROM declination WHERE word_category_id = ?', (id,))
    db.execute('DELETE FROM word_category WHERE id = ?', (id, ))

    db.commit()

    return redirect(url_for('language.categories'))


@bp.route('/category', methods=('GET', 'POST'))
@admin_required
def categories():
    db = get_db()

    categories = db.execute('SELECT * FROM word_category ORDER BY name ASC')

    return render_template('language/categories.html', categories=categories)
