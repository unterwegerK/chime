"""Script which launches dash app
"""
from chime_dash.app.run import DASH
from flask import send_file, request

from chime_dash.app.services.pdf_printer import print_to_pdf


if __name__ == "__main__":
    DASH.run_server(host="0.0.0.0")
