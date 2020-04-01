"""app/run

Defines the Dash instance
"""
from dash import Dash
from flask import send_file, request

from penn_chime.settings import DEFAULTS

from chime_dash.app.components import Body
from chime_dash.app.utils.callbacks import wrap_callbacks
from chime_dash.app.services.pdf_printer import print_to_pdf


LANGUAGE = "en"

BODY = Body(LANGUAGE, DEFAULTS)

DASH = Dash(
    __name__,
    external_stylesheets=BODY.external_stylesheets,
    external_scripts=BODY.external_scripts,
)
DASH.title = "Penn Medicine CHIME"  #! Should be moved into config / out of view
DASH.layout = BODY.html
wrap_callbacks(DASH)


@DASH.server.route("/download-as-pdf")
def download_as_pdf():
    """Serve a file from the upload directory."""
    pdf = print_to_pdf(LANGUAGE, request.args)
    return send_file(
        pdf, as_attachment=True, mimetype="pdf", attachment_filename="CHIME-report.pdf",
    )
