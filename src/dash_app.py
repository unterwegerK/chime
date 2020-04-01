"""Script which launches dash app
"""
from chime_dash.app.run import DASH
from flask import send_file, request

from chime_dash.app.services.pdf_printer import print_to_pdf


@DASH.server.route("/download-as-pdf")
def download_as_pdf():
    """Serve a file from the upload directory."""
    kwargs = dict()
    for key in BODY.callback_inputs:
        val = request.args.get(key, None)
        if val is not None:
            try:
                val = int(val) if val.isdigit() else float(val)
            except ValueError:
                pass
        kwargs[key] = val

    pdf = print_to_pdf(BODY.components["container"], kwargs)
    return send_file(
        pdf, as_attachment=True, mimetype="pdf", attachment_filename="CHIME-report.pdf",
    )


server = DASH.server

if __name__ == "__main__":
    DASH.run_server(host="0.0.0.0")
