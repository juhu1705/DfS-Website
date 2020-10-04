import os

from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY='219z4r34äc3ü696567ß50917325#897235jhkle65bju#5',
                            DATABASE=os.path.join(app.instance_path, 'dfs.sqlite'))

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.instance_path, 'assets/pictures/profile'), exist_ok=True)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import database
    database.init_app(app)

    from . import home
    app.register_blueprint(home.bp)

    from . import map
    app.register_blueprint(map.bp)

    from . import characters
    app.register_blueprint(characters.bp)

    from . import discussion
    app.register_blueprint(discussion.bp)

    from . import language
    app.register_blueprint(language.bp)

    from . import error_handling
    app.register_blueprint(error_handling.bp)

    from . import documents
    app.register_blueprint(documents.bp)

    return app
