import functools, os

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app, send_from_directory,
    send_file
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.database import get_db

bp = Blueprint('error', __name__)


@bp.app_errorhandler(400)
def error_400(error):
    """400 - Ungültige Anfrage"""
    return render_template("error.html", error="Du fragst zu viel, dabei ist dir wohl ein Fehler unterlaufen. Schade."), 400


@bp.app_errorhandler(403)
def error_403(error):
    """403 - Verboten"""
    return render_template("error.html", error="Du bist aber ein fieses Bürschchen, geh fort von hier!"), 403


@bp.app_errorhandler(404)
def error_404(error):
    """404 - Seite nicht gefunden"""
    return render_template("error.html", error="Diese Seite wurde nicht gefunden, vielleicht willst du ja woanders nach ihr suchen?"), 404


@bp.app_errorhandler(500)
def error_500(error):
    """500 - serverseitiger Fehler"""
    return render_template("error.html", error="Ich habe entschieden da nicht mitzuspielen!"), 500