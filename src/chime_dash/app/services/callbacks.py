from itertools import repeat
from typing import List
from datetime import datetime
from collections import OrderedDict
from urllib.parse import parse_qsl, urlencode
from dash import no_update
from dash.exceptions import PreventUpdate

from chime_dash.app.utils.callbacks import ChimeCallback, register_callbacks
from chime_dash.app.utils import (
    get_n_switch_values,
    prepare_visualization_group
)

from penn_chime.models import SimSirModel
from penn_chime.parameters import Parameters, Disposition


class ComponentCallbacks:
    def __init__(self, callbacks: List[ChimeCallback], component_instance):
        self._callbacks = callbacks
        self._component_instance = component_instance
        register_callbacks(self._callbacks)


class IndexCallbacks(ComponentCallbacks):

    @staticmethod
    def toggle_tables(switch_value):
        return get_n_switch_values(switch_value, 3)

    @staticmethod
    def get_parameters(inputs_dict) -> Parameters:
        """Reads html form outputs and converts them to a parameter instance

        Returns Parameters
        """
        dt = inputs_dict.get("doubling_time", None)
        dfh = inputs_dict["date_first_hospitalized"] if not dt else None
        return Parameters(
            population=inputs_dict["population"],
            current_hospitalized=inputs_dict["current_hospitalized"],
            date_first_hospitalized=dfh,
            doubling_time=dt,
            hospitalized=Disposition(
                inputs_dict["hospitalized_rate"] / 100, inputs_dict["hospitalized_los"]
            ),
            icu=Disposition(inputs_dict["icu_rate"] / 100, inputs_dict["icu_los"]),
            infectious_days=inputs_dict["infectious_days"],
            market_share=inputs_dict["market_share"] / 100,
            n_days=inputs_dict["n_days"],
            relative_contact_rate=inputs_dict["relative_contact_rate"] / 100,
            ventilated=Disposition(
                inputs_dict["ventilated_rate"] / 100, inputs_dict["ventilated_los"]
            ),
            max_y_axis=inputs_dict.get("max_y_axis_value", None),
        )

    @staticmethod
    def handle_inputs_changes(sidebar_data, intro_component):
        result = []
        if sidebar_data:
            pars = IndexCallbacks.get_parameters(sidebar_data)
            model = SimSirModel(pars)
            viz_kwargs = dict(
                labels=pars.labels,
                table_mod=7,
                max_y_axis=pars.max_y_axis,
            )
            result.extend(intro_component.build(model, pars))
            for df_key in ["admits_df", "census_df", "sim_sir_w_date_df"]:
                df = None
                if model:
                    df = model.__dict__.get(df_key, None)
                result.extend(prepare_visualization_group(df, **viz_kwargs))
        else:
            raise PreventUpdate
        return result

    def __init__(self, component_instance):
        def handle_inputs_changes_helper(sidebar_updated, sidebar_data):
            intro_component = component_instance.components["intro"]
            return IndexCallbacks.handle_inputs_changes(sidebar_data, intro_component)

        super().__init__(
            component_instance=component_instance,
            callbacks=[
                ChimeCallback(  # If user toggles show_tables, show/hide tables
                    changed_elements={"show_tables": "value"},
                    dom_updates={
                        "SIR_table_container": "hidden",
                        "new_admissions_table_container": "hidden",
                        "admitted_patients_table_container": "hidden",
                    },
                    callback_fn=IndexCallbacks.toggle_tables
                ),
                ChimeCallback(  # If the parameters or model change, update the text
                    changed_elements={"sidebar-store": "modified_timestamp"},
                    dom_updates={
                        "intro": "children",
                        "new_admissions_graph": "figure",
                        "new_admissions_table": "children",
                        "new_admissions_download": "href",
                        "admitted_patients_graph": "figure",
                        "admitted_patients_table": "children",
                        "admitted_patients_download": "href",
                        "SIR_graph": "figure",
                        "SIR_table": "children",
                        "SIR_download": "href",
                    },
                    callback_fn=handle_inputs_changes_helper,
                    state={"sidebar-store": "data"},
                )
            ]
        )


class SidebarCallbacks(ComponentCallbacks):

    @staticmethod
    def get_formated_values(i, input_values):
        result = OrderedDict(zip(i.input_value_map.keys(), input_values))
        for key, input_type in i.input_type_map.items():
            # todo remove this hack needed because of how Checklist type (used for switch input) returns values
            if input_type == "switch":
                result[key] = False if result[key] == [True] else True
            elif input_type == "date":
                value = result[key]
                try:
                    result[key] = datetime.strptime(value, "%Y-%m-%d").date() if value else value
                except ValueError:
                    pass
        return result

    def __init__(self, component_instance):
        def update_parameters_helper(*args, **kwargs):
            input_values = list(args)
            input_dict = OrderedDict(zip(component_instance.input_value_map.keys(), input_values))
            sidebar_data = input_values.pop(-1)
            if sidebar_data and input_dict and input_dict == sidebar_data:
                raise PreventUpdate
            return [SidebarCallbacks.get_formated_values(component_instance, input_values)]

        super().__init__(
            component_instance=component_instance,
            callbacks=[
                ChimeCallback(
                    changed_elements=component_instance.input_value_map,
                    dom_updates={"sidebar-store": "data"},
                    callback_fn=update_parameters_helper,
                    state={"sidebar-store": "data"},
                )
            ]
        )


# todo Add tons of tests and validation because there be dragons
class RootCallbacks(ComponentCallbacks):
    @staticmethod
    def try_parsing_number(v):
        if v == 'None':
            result = None
        else:
            try:
                result = int(v)
            except ValueError:
                try:
                    result = float(v)
                except ValueError:
                    result = v
        return result

    @staticmethod
    def get_inputs(val_dict, inputs_keys):
        # todo handle versioning of inputs
        return OrderedDict((key, value) for key, value in val_dict.items() if key in inputs_keys)

    @staticmethod
    def parse_hash(hash_str, sidebar_input_types):
        hash_dict = dict(parse_qsl(hash_str[1:]))
        result = OrderedDict()
        # Inputs are expected in order, use order from Sidebar vs parsed hash
        for key, value_type in sidebar_input_types.items():
            value = hash_dict[key]
            if value_type == "number":
                parsed_value = RootCallbacks.try_parsing_number(value)
            else:
                parsed_value = value
            result[key] = parsed_value
        return result

    @staticmethod
    def hash_changed(sidebar_input_types, hash_str=None, root_data=None):
        if hash_str:
            hash_dict = RootCallbacks.parse_hash(hash_str, sidebar_input_types)
            result = RootCallbacks.get_inputs(hash_dict, sidebar_input_types.keys())
            # Don't update the data store if it already contains the same data
            if result == root_data:
                raise PreventUpdate
        else:
            raise PreventUpdate
        return [result]

    @staticmethod
    def stores_changed(inputs_keys, root_mod, sidebar_mod, root_data, sidebar_data):
        root_modified = root_mod or 0
        sidebar_modified = sidebar_mod or 0
        # Data is the same, don't update either
        if root_data == sidebar_data:
            raise PreventUpdate
        # Sidebar data doesn't exist or root is newer, update the sidebar data
        elif (root_data and not sidebar_data) or (root_modified >= sidebar_modified):
            new_values = RootCallbacks.get_inputs(root_data, inputs_keys)
            result = [no_update] + list(new_values.values())
        # Root data doesn't exist or sidebar is newer, update the root data
        elif (sidebar_data and not root_data) or (root_modified < sidebar_modified):
            new_val = RootCallbacks.get_inputs(sidebar_data, inputs_keys)
            result = ["#{}".format(urlencode(new_val))]
            for _ in repeat(None, len(new_val)):
                result.append(no_update)
        else:
            raise RuntimeError("Unexpected state")
        return result

    def __init__(self, component_instance):
        sidebar = component_instance.components["sidebar"]
        sidebar_inputs = sidebar.input_value_map
        sidebar_input_types = sidebar.input_type_map

        def hash_changed_helper(hash_str=None, root_data=None):
            return RootCallbacks.hash_changed(sidebar_input_types, hash_str, root_data)

        def stores_changed_helper(root_mod, sidebar_mod, root_data, sidebar_data):
            return RootCallbacks.stores_changed(sidebar_inputs.keys(), root_mod, sidebar_mod, root_data, sidebar_data)
        super().__init__(
            component_instance=component_instance,
            callbacks=[
                ChimeCallback(
                    changed_elements={"location": "hash"},
                    dom_updates={"root-store": "data"},
                    callback_fn=hash_changed_helper,
                    state={"root-store": "data"},
                ),
                ChimeCallback(
                    changed_elements={"root-store": "modified_timestamp", "sidebar-store": "modified_timestamp"},
                    dom_updates={"location": "hash", **sidebar_inputs},
                    callback_fn=stores_changed_helper,
                    state={"root-store": "data", "sidebar-store": "data"},
                ),
            ]
        )
