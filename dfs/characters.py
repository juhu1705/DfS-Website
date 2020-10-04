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

bp = Blueprint('characters', __name__, url_prefix='/characters')


@bp.route('/')
def index():
    db = get_db()

    enfali = db.execute('SELECT * FROM characters c, user_permissions up'
                        ' WHERE c.id = up.character_id AND species = "Enfali" ORDER BY name DESC').fetchall()
    nithriln = db.execute('SELECT * FROM characters c, user_permissions up'
                          ' WHERE c.id = up.character_id AND species = "Nithriln" ORDER BY name DESC').fetchall()
    menschen = db.execute('SELECT * FROM characters c, user_permissions up'
                          ' WHERE c.id = up.character_id AND species = "Mensch" ORDER BY name DESC').fetchall()
    zwerge = db.execute('SELECT * FROM characters c, user_permissions up'
                        ' WHERE c.id = up.character_id AND species = "Zwerg" ORDER BY name DESC').fetchall()
    elfen = db.execute('SELECT * FROM characters c, user_permissions up'
                       ' WHERE c.id = up.character_id AND species = "Elf" ORDER BY name DESC').fetchall()
    drachen = db.execute('SELECT * FROM characters c, user_permissions up'
                         ' WHERE c.id = up.character_id AND species = "Drache" ORDER BY name DESC').fetchall()

    return render_template('characters/characters.html', enfali=enfali,
                           nithriln=nithriln, menschen=menschen, zwerge=zwerge, elfen=elfen, drachen=drachen)


@bp.route('/<int:id>', methods=('GET', 'POST') )
def character(id):
    db = get_db()
    character = db.execute('SELECT * FROM characters c, user_permissions up'
                           ' WHERE c.id = up.character_id AND c.id = ?', (id, )).fetchone()
    all_character_information = db.execute('SELECT * FROM character_information ci, information_order io'
                                           ' WHERE ci.character_id = ? AND io.information_title = ci.title'
                                           ' ORDER BY io.position ASC', (id, )).fetchall()
    return render_template('characters/character.html', all_character_information=all_character_information,
                           character=character)


def is_valid_species(species):
    return species == 'Enfali' or species == 'Nithriln' or species == 'Mensch'\
           or species == 'Zwerg' or species == 'Elf' or species == 'Drache'


@bp.route('/create', methods=('GET', 'POST'))
@writer_required
def create():
    db = get_db()

    if request.method == 'POST':
        try:
            name = request.form['name']
            family = request.form['family']
            species = request.form['species']
        except:
            flash('Deine mitgegebenen Daten konnten nicht gefunden werden. Bitte versuche es noch einmal.')
            return render_template('characters/create.html')

        if not species or not family or not name:
            flash('Sie haben nicht alle Werte angegeben!')
            return render_template('characters/create.html')

        if not is_valid_species(species):
            flash('Diese species existiert nicht!')
            return render_template('characters/create.html')

        character = db.execute('SELECT * FROM characters'
                               ' WHERE name = ? AND family = ? and species = ?', (name, family, species, )).fetchone()

        if character is not None:
            flash('Dieser Charakter existiert bereits!')
            return render_template('characters/create.html')

        db.execute('INSERT INTO characters (name, family, species) VALUES (?, ?, ?)', (name, family, species))
        character = db.execute('SELECT * FROM characters'
                               ' WHERE name = ? AND family = ? AND species = ?', (name, family, species)).fetchone()
        db.execute('INSERT INTO user_permissions (user_id, character_id)'
                   ' VALUES (?, ?)', (g.user['id'], character['id']))
        db.commit()

        return redirect(url_for('characters.index'))

    return render_template('characters/create.html')


@bp.route('/<int:id>/edit', methods=('GET', 'POST'))
@writer_required
def edit_character(id):
    db = get_db()

    character_exists = db.execute('SELECT * FROM user_permissions WHERE user_id = ? AND character_id = ?', (g.user['id'], id)).fetchone()

    if g.user['level'] < 2 and character_exists is None:
        flash('Du benötigst höhere Berechtigungen!')
        return redirect(url_for('characters.index'))

    tags = db.execute('SELECT * FROM information_order ORDER BY position ASC').fetchall()
    c_tags = db.execute('SELECT * FROM information_order, character_information'
                        ' WHERE character_id = ? AND information_title = title'
                        ' ORDER BY position ASC', (id,)).fetchall()

    if request.method == 'POST':
        if 'add_tag' in request.form:
            flash('Funktion noch nicht verfügbar.')
            return render_template('characters/create.html')

        try:
            name = request.form['name']
            family = request.form['family']
            species = request.form['species']
        except:
            flash('Deine mitgegebenen Daten konnten nicht gefunden werden. Bitte versuche es noch einmal.')
            return render_template('characters/create.html')

        if not species or not family or not name:
            flash('Sie haben nicht alle Werte angegeben!')
            return render_template('characters/create.html')

        if not is_valid_species(species):
            flash('Diese species existiert nicht!')
            return render_template('characters/create.html')

        character = db.execute('SELECT * FROM characters'
                               ' WHERE id = ?', (id, )).fetchone()
        if character is None:
            flash('Dieser Charakter existiert nicht!')
            return render_template('characters/create.html')

        db.execute('UPDATE characters SET name = ?, family = ?, species = ? WHERE id = ?', (name, family, species, id))

        for c_tag in c_tags:

            if str(c_tag['information_title']) + '.' + str(c_tag['value']) in request.form \
                    and str(c_tag['information_title']) + '.' + str(c_tag['value']) + '.value' in request.form:
                tag_name = request.form[str(c_tag['information_title']) + '.' + str(c_tag['value'])]
                value = request.form[str(c_tag['information_title']) + '.' + str(c_tag['value']) + '.value']

                if value != '':
                    tag = db.execute('SELECT * FROM information_order WHERE information_title = ?', (tag_name,)).fetchone()

                    if tag is not None:
                        db.execute('UPDATE character_information SET value = ?, title = ?, character_id=? WHERE id=?',
                                   (value, tag_name, id, c_tag['id']))
                    else:
                        flash('Dieser Tag wurde nicht gefunden.')
                else:
                    db.execute('DELETE FROM character_information WHERE id = ?', (c_tag['id'],))

        if 'select_tag' in request.form and 'tag' in request.form:
            tag_name = str(request.form['select_tag'])
            value = str(request.form['tag'])

            if value != '':
                tag = db.execute('SELECT * FROM information_order WHERE information_title = ?', (tag_name, )).fetchone()

                if tag is not None:
                    db.execute('INSERT INTO character_information (value, title, character_id) VALUES (?, ?, ?)',
                               (value, tag_name, id))
                else:
                    flash('Dieser Tag wurde nicht gefunden.')

        db.commit()

    tags = db.execute('SELECT * FROM information_order ORDER BY position DESC').fetchall()
    c_tags = db.execute('SELECT * FROM information_order, character_information'
                        ' WHERE character_id = ? AND information_title = title'
                        ' ORDER BY position ASC', (id,)).fetchall()
    character = db.execute('SELECT * FROM characters c, user_permissions up WHERE c.id = up.character_id AND c.id = ?',
                           (id, )).fetchone()

    return render_template('characters/edit_character.html', tags=tags, character=character, c_tags=c_tags)


@bp.route('/tags')
@writer_required
def tags():
    db = get_db()
    tags = db.execute('SELECT * FROM information_order ORDER BY position ASC').fetchall()
    return render_template('characters/tags.html', tags=tags)


@bp.route('/tag/<int:position>/up')
@writer_required
def tag_up(position):
    db = get_db()
    tags = db.execute('SELECT * FROM information_order ORDER BY position DESC').fetchall()

    for tag in tags:
        if tag['position'] == position - 1:
            db.execute('DELETE FROM information_order WHERE position = ?', (tag['position'], ))
            db.execute('UPDATE information_order SET position = ? WHERE position = ?', (position - 1, position))
            db.execute('INSERT INTO information_order (position, information_title) VALUES (?, ?)',
                       (position, tag['information_title']))
            db.commit()

    return redirect(url_for('characters.tags'))


@bp.route('/tag/<int:position>/down')
@writer_required
def tag_down(position):
    db = get_db()
    tags = db.execute('SELECT * FROM information_order ORDER BY position DESC').fetchall()

    for tag in tags:
        if tag['position'] == position + 1:
            db.execute('DELETE FROM information_order WHERE position = ?', (tag['position'],))
            db.execute('UPDATE information_order SET position = ? WHERE position = ?', (position + 1, position))
            db.execute('INSERT INTO information_order (position, information_title) VALUES (?, ?)',
                       (position, tag['information_title']))
            db.commit()

    return redirect(url_for('characters.tags'))


@bp.route('tags/create_tag', methods=('GET', 'POST'))
@writer_required
def create_tag_in_tags():
    if request.method == 'POST':
        try:
            name = request.form['name']
        except:
            flash('Deine mitgegebenen Daten konnten nicht gefunden werden. Bitte versuche es noch einmal.')
            return render_template('characters/add_tag.html')

        if not name:
            flash('Sie haben keinen Werte angegeben!')
            return render_template('characters/add_tag.html')

        db = get_db()

        character = db.execute('SELECT * FROM information_order'
                               ' WHERE information_title = ? ', (name, )).fetchone()

        if character is not None:
            flash('Dieser Tag existiert bereits!')
            return render_template(url_for('characters.tags'))

        db.execute('INSERT INTO information_order (information_title, position)'
                   ' VALUES (?, (SELECT MAX(position) FROM information_order) + 1)', (name, ))
        db.commit()

        return redirect(url_for('characters.tags'))

    return render_template('characters/add_tag.html')


@bp.route('character/<int:id>/create_tag', methods=('GET', 'POST'))
@writer_required
def create_tag(id):
    if request.method == 'POST':
        try:
            name = request.form['name']
        except:
            flash('Deine mitgegebenen Daten konnten nicht gefunden werden. Bitte versuche es noch einmal.')
            return render_template('characters/add_tag.html')

        if not name:
            flash('Sie haben keinen Werte angegeben!')
            return render_template('characters/add_tag.html')

        db = get_db()

        character = db.execute('SELECT * FROM information_order'
                               ' WHERE information_title = ? ', (name, )).fetchone()

        if character is not None:
            flash('Dieser Tag existiert bereits!')
            return render_template('characters/create.html')

        db.execute('INSERT INTO information_order (information_title, position)'
                   ' VALUES (?, (SELECT MAX(position) FROM information_order) + 1)', (name, ))
        db.commit()

        return redirect(url_for('characters.character', id=id))

    return render_template('characters/add_tag.html')


@bp.route('/tag/<int:position>/delete')
@writer_required
def delete_tag(position):
    db = get_db()
    tag = db.execute('SELECT * FROM information_order WHERE position = ?', (position, )).fetchone()
    db.execute('DELETE FROM character_information WHERE title = ?', (tag['information_title'], ))
    db.execute('DELETE FROM information_order WHERE position = ?', (position, ))
    db.commit()
    return redirect(url_for('characters.tags'))


@bp.route('/character/<int:id>/delete')
@writer_required
def delete_character(id):
    db = get_db()

    character_exists = db.execute('SELECT * FROM user_permissions WHERE user_id = ? AND character_id = ?',
                                  (g.user['id'], id)).fetchone()

    if g.user['level'] < 2 and character_exists is None:
        flash('Du benötigst höhere Berechtigungen!')
        return redirect(url_for('characters.index'))

    db = get_db()

    db.execute('DELETE FROM character_information WHERE character_id = ?', (id, ))
    db.execute('DELETE FROM user_permissions WHERE character_id = ?', (id, ))
    db.execute('DELETE FROM characters WHERE id = ?', (id, ))

    db.commit()
    return redirect(url_for('characters.index'))
