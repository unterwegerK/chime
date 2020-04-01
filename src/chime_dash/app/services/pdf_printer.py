"""Utilities for exporting dash app to pdf
"""
import json
import base64

from time import sleep

from io import BytesIO

from json import dumps
from selenium import webdriver

from dash import Dash
from dash.testing.application_runners import ThreadedRunner
from dash.testing.composite import DashComposite
from dash_bootstrap_components import Container, Row
from dash_html_components import Div

from chime_dash.app.utils import parameters_deserializer
from chime_dash.app.pages.index import Index
from chime_dash.app.pages.sidebar import Sidebar
from chime_dash.app.components import EXTERNAL_STYLESHEETS, EXTERNAL_SCRIPTS
from chime_dash.app.utils.callbacks import wrap_callbacks


def send_devtools(driver, cmd, params=None):
    params = params or None
    resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
    url = driver.command_executor._url + resource
    body = json.dumps({"cmd": cmd, "params": params})
    response = driver.command_executor._request("POST", url, body)
    if response.get("status", False):
        raise Exception(response.get("value"))
    return response.get("value")


def save_as_pdf(driver, options=None):
    """Saves pdf to buffer object
    """
    options = options or {}
    # https://timvdlippe.github.io/devtools-protocol/tot/Page#method-printToPDF
    result = send_devtools(driver, "Page.printToPDF", options)

    cached_file = BytesIO()
    cached_file.write(base64.b64decode(result["data"]))
    cached_file.seek(0)
    return cached_file


def print_to_pdf(language, kwargs):
    """Extracts content and prints pdf to buffer object.
    """
    app = Dash(
        __name__,
        external_stylesheets=EXTERNAL_STYLESHEETS,
        external_scripts=EXTERNAL_SCRIPTS,
    )

    defaults = parameters_deserializer(Sidebar.update_parameters(**kwargs)[0])
    sidebar = Sidebar(language, defaults).html[0]
    index = Index(language, defaults).html[0]

    sidebar.width = 0
    sidebar.hidden = True
    index.width = 12

    layout = Div(
        children=[  # self.components["navbar"].html
            Container(children=Row([sidebar, index]), fluid=True)
        ]
    )

    app.layout = layout
    app.title = "CHIME Printer"
    # wrap_callbacks(app)

    # outputs = component.callback(**kwargs)
    #
    # @app.callback(component.callback_outputs, list(component.callback_inputs.values()))
    # def callback(*args):  # pylint: disable=W0612, W0613
    #     return outputs

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")

    with ThreadedRunner() as starter:
        with DashComposite(starter, browser="Chrome", options=[chrome_options]) as dc:
            dc.start_server(app, port=8051)
            while "Loading..." in dc.driver.page_source:
                sleep(1)
            pdf = save_as_pdf(dc.driver, {"landscape": False})
            dc.driver.quit()

    return pdf
