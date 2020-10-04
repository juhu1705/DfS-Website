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

bp = Blueprint('map', __name__, url_prefix='/map')

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/')
def index():
    maps = get_maps()

    print(maps)

    if maps is None:
        return redirect('home.index')

    return render_template('map/map.html', maps=maps)


@bp.route('/upload', methods=('GET', 'POST'))
@writer_required
def upload_map():
    if request.method == 'POST':
        if 'image_loader' in request.files:
            file = request.files['image_loader']
            try:
                name = request.form['filename']
            except:
                flash('Du hast keinen Namen angegeben.')
                return redirect(url_for('home.index'))

            if file.filename == '':
                return redirect(url_for('map.index'))

            if file and allowed_file(file.filename) and check_map_name(name, file.filename.rsplit('.')[1].lower()):
                filename = secure_filename(file.filename)

                path = os.path.join(current_app.instance_path, 'assets/pictures/maps')

                os.makedirs(path, exist_ok=True)

                file.save(os.path.join(path, name + '.' + filename.rsplit('.')[1].lower()))
        return redirect(url_for('map.index'))
    return render_template('map/add_map.html')


def check_map_name(name, extension):
    if os.path.exists(os.path.join(current_app.instance_path, 'assets/pictures/maps')):
        for file in os.listdir(os.path.join(current_app.instance_path, 'assets/pictures/maps')):
            if file == name + '.' + extension:
                return False
    return True


def get_maps():
    if os.path.exists(os.path.join(current_app.instance_path, 'assets/pictures/maps')):
        files = []
        for file in os.listdir(os.path.join(current_app.instance_path, 'assets/pictures/maps')):
            files.append(file)
        return files
    else:
        return None


@bp.route('/map/<name>')
def send_map(name):
    path = os.path.join(current_app.instance_path, 'assets/pictures/maps')

    if os.path.exists(path) and os.path.exists(os.path.join(path, name)):
        path_extended = os.path.join(current_app.instance_path, os.path.join('assets/pictures/maps', name))
        print(path_extended)
        return send_file(path_extended)
    else:
        return send_from_directory('static', 'pictures/blank.png')


@bp.route('/map/<name>/delete')
def delete(name):
    path = os.path.join(current_app.instance_path, 'assets/pictures/maps')

    if os.path.exists(path) and os.path.exists(os.path.join(path, name)):
        path_extended = os.path.join(current_app.instance_path, os.path.join('assets/pictures/maps', name))
        print(path_extended)
        os.remove(path_extended)

    return redirect(url_for('map.index'))

