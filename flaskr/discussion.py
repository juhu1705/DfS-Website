import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.database import get_db
from flaskr.auth import login_required, admin_required, getAdminKey

bp = Blueprint('discussions', __name__, url_prefix='/discussions')


@bp.route('/', methods=('GET', 'POST'))
def index():
    db = get_db()
    discussions = db.execute('SELECT d.title, u.name, d.created, d.id, d.author FROM discussion d, user u '
                             'WHERE d.author = u.id ORDER BY d.created DESC').fetchall()
    return render_template('discussion/discussion.html', discussions=discussions)


@bp.route('/open_discussion', methods=('GET', 'POST'))
@login_required
def open_discussion():
    db = get_db()

    if request.method == 'POST':
        try:
            title = request.form['theme']
        except:
            flash('Post incorrect!')
            return redirect(url_for('home.index'))

        if len(title) > 25:
            flash('Bitte wählen sie einen kürzeren Titel!')
            return render_template('discussion/create_discussion.html')

        if title:
            import time

            db.execute('INSERT INTO discussion (title, author, created) '
                       'VALUES (?, ?, ?)', (title, g.user['id'], time.strftime('%Y-%m-%d %H:%M:%S')))
            db.commit()
            return redirect(url_for('discussions.index'))

    return render_template('discussion/create_discussion.html')


@bp.route('/discussion/<int:id>', methods=('GET', 'POST'))
def discussion(id):
    db = get_db()

    comments = db.execute('SELECT c.created, c.value, u.name, c.author, c.id, c.discussion_id FROM comment c, user u'
                          ' WHERE c.discussion_id = ? AND c.author = u.id ORDER BY c.created DESC', (id,)).fetchall()
    discussion = db.execute('SELECT d.title, u.name, d.created, d.id, d.author FROM discussion d, user u '
                            'WHERE d.author = u.id AND d.id = ?', (id,)).fetchone()

    if not discussion:
        abort(404)
        return

    if request.method == 'POST':
        try:
            title = request.form['theme']
        except:
            flash('Post incorrect!')
            return redirect(url_for('home.index'))
        if title:
            import time

            db.execute('INSERT INTO discussion (title, author, created) '
                       'VALUES (?, ?, ?)', (title, g.user['id'], time.strftime('%Y-%m-%d %H:%M:%S')))
            db.commit()
            return redirect(url_for('discussions.index'))

    return render_template('discussion/comment_overview.html', comments=comments, discussion=discussion)


@bp.route('discussion/<int:discussion_id>/create_comment', methods=('GET', 'POST'))
@login_required
def create_comment(discussion_id):
    db = get_db()

    if request.method == 'POST':
        try:
            title = request.form['value']
        except:
            flash('Post incorrect!')
            return redirect(url_for('home.index'))
        if title:
            import time

            db.execute('INSERT INTO comment (value, author, created, discussion_id) '
                       'VALUES (?, ?, ?, ?)', (title, g.user['id'], time.strftime('%Y-%m-%d %H:%M:%S'), discussion_id))
            db.commit()
            return redirect(url_for('discussions.discussion', id=discussion_id))

    return render_template('discussion/create_comment.html')


@bp.route('discussion/<int:discussion_id>/comment/<int:id>', methods=('GET', 'POST'))
@login_required
def comment(discussion_id, id):
    db = get_db()

    comment = db.execute('SELECT * FROM comment WHERE id = ?', (id,)).fetchone()
    discussion = db.execute('SELECT d.title, u.name, d.created, d.id, d.author FROM discussion d, user u '
                            'WHERE d.author = u.id AND d.id = ?', (discussion_id,)).fetchone()

    if discussion is None or comment is None:
        abort(404)
        return

    if g.user['id'] != comment['author'] and g.user['id'] != discussion['author'] and g.user['level'] < getAdminKey():
        return redirect(url_for('discussions.discussion', id=discussion_id))

    if request.method == 'POST':
        try:
            title = request.form['value']
        except:
            flash('Post incorrect!')
            return redirect(url_for('home.index'))
        if title:
            import time

            db.execute('UPDATE comment SET value = ?, author = ?, created = ? '
                       'WHERE id = ?', (title, g.user['id'], time.strftime('%Y-%m-%d %H:%M:%S'), id))
            db.commit()
            return redirect(url_for('discussions.discussion', id=discussion_id))

    return render_template('discussion/edit_comment.html', comment=comment, discussion=discussion)


@bp.route('/discussion/<int:discussion_id>/comment/<int:id>/delete', methods=('GET', 'POST'))
@login_required
def delete_comment(discussion_id, id):
    db = get_db()

    comment = db.execute('SELECT * FROM comment WHERE id = ?', (id,)).fetchone()
    discussion = db.execute('SELECT d.title, u.name, d.created, d.id, d.author FROM discussion d, user u '
                            'WHERE d.author = u.id AND d.id = ?', (discussion_id,)).fetchone()

    if g.user['id'] != comment['author'] and g.user['id'] != discussion['author'] and g.user['level'] < getAdminKey():
        return redirect(url_for('discussions.discussion', id=discussion_id))

    db.execute('DELETE FROM comment WHERE id = ?', (id,))
    db.commit()

    return redirect(url_for('discussions.discussion', id=discussion_id))


@bp.route('/discussion/<int:id>/delete', methods=('GET', 'POST'))
@login_required
def delete_discussion(id):
    db = get_db()

    discussion = db.execute('SELECT d.title, u.name, d.created, d.id, d.author FROM discussion d, user u '
                            'WHERE d.author = u.id AND d.id = ?', (id,)).fetchone()

    if g.user['id'] != discussion['author'] and g.user['level'] < getAdminKey():
        return redirect(url_for('discussions.index'))

    db.execute('DELETE FROM discussion WHERE id = ?', (id, ))
    db.execute('DELETE FROM comment WHERE discussion_id = ?', (id,))
    db.commit()

    return redirect(url_for('discussions.index'))
