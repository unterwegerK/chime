"""app/run

Defines the Dash instance
"""
from dash import Dash
from flask import send_file, request, Flask

from penn_chime.settings import DEFAULTS

from chime_dash.app.components import Body, EXTERNAL_SCRIPTS, EXTERNAL_STYLESHEETS
from chime_dash.app.utils import get_new_defaults
from chime_dash.app.utils.callbacks import wrap_callbacks
from chime_dash.app.services.pdf_printer import print_to_pdf


LANGUAGE = "en"

BODY = Body(LANGUAGE, DEFAULTS)

DASH = Dash(
    __name__,
    external_stylesheets=EXTERNAL_STYLESHEETS,
    external_scripts=EXTERNAL_SCRIPTS,
)
DASH.title = "Penn Medicine CHIME"  #! Should be moved into config / out of view
DASH.layout = BODY.html
wrap_callbacks(DASH)


@DASH.server.route("/load")
def dash():

    print("Rounting '/load'")

    index = DASH.index()
    if request.args:
        defaults = get_new_defaults(DEFAULTS, **request.args)
        print(defaults)
        BODY.defaults = defaults
        DASH.layout = BODY.html
        index = DASH.index()

    return index


@DASH.server.route("/download-as-pdf")
def download_as_pdf():
    """Serve a file from the upload directory."""
    pdf = print_to_pdf(LANGUAGE, **request.args)
    return send_file(
        pdf, as_attachment=True, mimetype="pdf", attachment_filename="CHIME-report.pdf",
    )
