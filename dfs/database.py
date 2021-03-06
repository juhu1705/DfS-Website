import sqlite3

import click

from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import check_password_hash, generate_password_hash


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'],
                               detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    click.echo('Initialized the database.')


@click.command("make-admin")
@click.argument("name", type=click.STRING)
@click.option("--admin", type=click.INT)
@with_appcontext
def add_teacher(name, admin=2):
    user = get_db().execute('SELECT * FROM user WHERE name = ?', (name, )).fetchone()
    if not user:
        click.echo('Was, das wollen sie wirklich tun? Einen unschuldigen Benutzer verdoppeln. NIEMALS!')
        return 1

    get_db().execute('UPDATE user SET level=? WHERE name=?', (admin, name))
    get_db().commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(add_teacher)
