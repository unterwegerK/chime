"""components/sidebar
Initializes the side bar containing the various inputs for the model

#! _INPUTS should be considered for moving else where
"""
import dash_html_components as dhc

from typing import List, Dict, Any, Tuple
from collections import OrderedDict

from dash.dependencies import Input as CallbackInput, Output as CallbackOutput
from dash.development.base_component import ComponentMeta
from dash_core_components import Location

from penn_chime.defaults import RateLos
from penn_chime.parameters import Parameters

from chime_dash.app.components.base import Component
from chime_dash.app.utils.templates import create_switch_input, create_number_input, create_header, create_button

FLOAT_INPUT_MIN = 0.001
FLOAT_INPUT_STEP = "any"

_INPUTS = OrderedDict(
    regional_parameters={"type": "header", "size": "h3"},
    market_share={"type": "number", "min": FLOAT_INPUT_MIN, "step": FLOAT_INPUT_STEP, "max": 100.0, "percent": True},
    susceptible={"type": "number", "min": 1, "step": 1},
    known_infected={"type": "number", "min": 0, "step": 1},
    current_hospitalized={"type": "number", "min": 0, "step": 1},
    spread_and_contact={"type": "header", "size": "h3"},
    doubling_time={"type": "number", "min": FLOAT_INPUT_MIN, "step": FLOAT_INPUT_STEP},
    relative_contact_rate={
        "type": "number",
        "min": 0.0,
        "step": FLOAT_INPUT_STEP,
        "max": 100.0,
        "percent": True,
    },
    severity_parameters={"type": "header", "size": "h3"},
    hospitalized_rate={
        "type": "number",
        "min": 0.0,
        "step": FLOAT_INPUT_STEP,
        "max": 100.0,
        "percent": True,
    },
    icu_rate={
        "type": "number",
        "min": 0.0,
        "step": FLOAT_INPUT_STEP,
        "max": 100.0,
        "percent": True
    },
    ventilated_rate={
        "type": "number",
        "min": 0.0,
        "step": FLOAT_INPUT_STEP,
        "max": 100.0,
        "percent": True,
    },
    hospitalized_los={"type": "number", "min": 0, "step": 1},
    icu_los={"type": "number", "min": 0, "step": 1},
    ventilated_los={"type": "number", "min": 0, "step": 1},
    display_parameters={"type": "header", "size": "h3"},
    n_days={"type": "number", "min": 30, "step": 1},
    max_y_axis_value={"type": "number", "min": 10, "step": 10, "value": None},
    as_date={"type": "switch", "value": False},
    show_tables={"type": "switch", "value": False},
    show_tool_details={"type": "switch", "value": False},
    show_additional_projections={"type": "switch", "value": False},
    save_parameters={"type": "button", "value": "Save"},
)


class Sidebar(Component):
    """Sidebar to the left of the screen
    contains the various inputs used to interact
    with the model.
    """
    # localization temp. for widget descriptions
    localization_file = "sidebar.yml"

    callback_inputs = OrderedDict(
        [('hash', CallbackInput('location', 'hash'))] +
        [(key, CallbackInput(component_id=key, component_property="value"))
         for key in _INPUTS if _INPUTS[key]["type"] not in ("header", )]
    )

    callback_outputs = [
        CallbackOutput(component_id="inputs-container", component_property="children")
    ]

    @staticmethod
    def try_casting_number(v):
        try:
            return int(v)
        except ValueError:
            try:
                return float(v)
            except ValueError:
                return v

    @staticmethod
    def parse_form_parameters(**kwargs) -> Tuple[Parameters, Dict[str, Any]]:
        """Reads html form outputs and converts them to a parameter instance

        Returns Parameters and as_date argument
        """
        pars = Parameters(
            current_hospitalized=kwargs["current_hospitalized"],
            doubling_time=kwargs["doubling_time"],
            known_infected=kwargs["known_infected"],
            market_share=kwargs["market_share"] / 100,
            relative_contact_rate=kwargs["relative_contact_rate"] / 100,
            susceptible=kwargs["susceptible"],
            hospitalized=RateLos(
                kwargs["hospitalized_rate"] / 100, kwargs["hospitalized_los"]
            ),
            icu=RateLos(kwargs["icu_rate"] / 100, kwargs["icu_los"]),
            ventilated=RateLos(
                kwargs["ventilated_rate"] / 100, kwargs["ventilated_los"]
            ),
            max_y_axis=kwargs["max_y_axis_value"],
            n_days=kwargs["n_days"],
        )
        return pars

    @staticmethod
    def parse_hash(url_hash):
        params = [param.split("=") for param in url_hash[1:].split(";") if "=" in param]
        # todo change this over to something like `urlparse.parse_qs`
        return {item.split("=")[0]: Sidebar.try_casting_number(item.split("=")[1]) for item in url_hash[1:].split(";") if "=" in item}

    def build_inputs_helper(self, values={}):
        elements = []
        for idx, data in _INPUTS.items():
            data_dict = data.copy()
            if idx in values:
                data_dict['value'] = values[idx]
            elif "_" + idx + "-false" in values:
                # The switch components have an ID like "_as_date-false" instead of "as_date"
                data_dict['value'] = True if values["_" + idx + "-false"] == "on" else False

            if data_dict["type"] == "number":
                element = create_number_input(idx, data_dict, self.content, self.defaults)
            elif data_dict["type"] == "switch":
                element = create_switch_input(idx, data_dict, self.content)
            elif data_dict["type"] == "header":
                element = create_header(idx, self.content)
            elif data_dict["type"] == "button":
                element = create_button(idx, self.content)
            else:
                raise ValueError(
                    "Failed to parse input '{idx}' with data '{data}'".format(
                        idx=idx, data=data
                    )
                )
            elements.append(element)
        return elements

    def get_html(self) -> List[ComponentMeta]:
        """Initializes the view
        """
        elements = self.build_inputs_helper()

        sidebar = dhc.Div(
            children=[
                Location(id='location'),
                dhc.Nav(
                    children=dhc.Div(
                        id="inputs-container",
                        children=elements,
                        className="p-4",
                        style={
                            "height": "calc(100vh - 48px)",
                            "overflowY": "auto",
                        },
                    ),
                    className="col-md-3",
                    style={
                        "position": "fixed",
                        "top": "48px",
                        "bottom": 0,
                        "left": 0,
                        "zIndex": 100,
                        "boxShadow": "inset -1px 0 0 rgba(0, 0, 0, .1)"
                    }
                )
            ]
        )

        return [sidebar]

    def callback(self, *args, **kwargs):
        result = []
        if "hash" in kwargs:
            result.append(self.build_inputs_helper(Sidebar.parse_hash(kwargs["hash"])))
        return result
