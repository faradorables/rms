from flask import render_template, flash, redirect, url_for
from . import main
from flask_wtf.csrf import CSRFError

# @app.errorhandler(CSRFError)
# def handle_csrf_error(e):
#     return render_template('error/400.html', reason=e.description), 400

@main.app_errorhandler(403)
def forbidden(e):
    flash(u'Maaf halaman yang anda cari tak ditemukan.', 'danger')
    return redirect(url_for('main.index'))
    # return render_template('error/403.html'), 403

@main.app_errorhandler(404)
def page_not_found(e):
    flash(u'Maaf halaman yang anda cari tak ditemukan.', 'danger')
    return redirect(url_for('main.index'))
    # return render_template('error/404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    flash(u'Maaf halaman yang anda cari tak ditemukan.', 'danger')
    return redirect(url_for('main.index'))
    # return render_template('error/500.html'), 500