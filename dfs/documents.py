import functools
import os

from flask import (
    Blueprint, flash, g, redirect, render_template, url_for, current_app, send_from_directory,
    send_file
)

from dfs.database import get_db

bp = Blueprint('document', __name__, url_prefix='/document')

@bp.route('/')
def index():
    flash('Diese Seite wird in Zukunft hinzugefügt!')

    return redirect(url_for('home.index'))


@bp.route('/<int:id>')
def story(id):
    db = get_db()

    document = db.execute('SELECT * FROM short_story WHERE id = ?', (id, )).fetchone()

    return render_template('short_stories/document.html', document=document)
