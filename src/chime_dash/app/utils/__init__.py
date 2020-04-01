"""app/utils
utils
The helper classes and functions here exist to reduce large repetitive code
blocks throughout the project. They may contain functions or classes from
module but do not change the parameters of the class
Modules
-------
templates       utilities for localization templates
"""
from . import callbacks
from . import templates

from itertools import repeat
from urllib.parse import quote
from json import dumps, loads
from typing import Any, List
from datetime import date, datetime
from dateutil.parser import parse as parse_date
from pandas import DataFrame

from chime_dash.app.services.plotting import plot_dataframe
from chime_dash.app.utils.templates import df_to_html_table

from penn_chime.parameters import Parameters, Disposition
from penn_chime.constants import DATE_FORMAT
from penn_chime.charts import build_table


def _parameters_serializer_helper(obj):
    if isinstance(obj, (datetime, date)):
        result = obj.isoformat()
    else:
        result = obj.__dict__
    return result


# todo handle versioning? we don"t currently persist Dash state, but we may. ¯\_(ツ)_/¯
def parameters_serializer(p: Parameters):
    return dumps(p, default=_parameters_serializer_helper, sort_keys=True)


def parameters_deserializer(p_json: str, **kwargs):
    values = loads(p_json)
    values.update(kwargs)
    dfh = (
        parse_date(values["date_first_hospitalized"]).date()
        if values["date_first_hospitalized"]
        else None
    )
    result = Parameters(
        current_hospitalized=int(values["current_hospitalized"]),
        hospitalized=Disposition(*values["hospitalized"]),
        icu=Disposition(*values["icu"]),
        relative_contact_rate=float(values["relative_contact_rate"]),
        ventilated=Disposition(*values["ventilated"]),
        current_date=parse_date(values["current_date"]).date(),
        date_first_hospitalized=dfh,
        doubling_time=float(values["doubling_time"]),
        infectious_days=int(values["infectious_days"]),
        market_share=float(values["market_share"]),
        max_y_axis=int(values["max_y_axis"])
        if values["max_y_axis"] is not None
        else None,
        n_days=int(values["n_days"]),
        population=int(values["population"]),
        recovered=int(values["recovered"]),
        region=values["region"] if values["region"] else None,
    )

    for key, value in values.items():

        if result.__dict__[key] != value and key not in (
            "dispositions",
            "hospitalized",
            "icu",
            "ventilated",
            "current_date",
            "date_first_hospitalized",
        ):
            result.__dict__[key] = value

    return result


def get_new_defaults(defaults: Parameters, **kwargs):
    """
    """
    for key in ["hospitalized", "icu", "ventilated"]:
        rate = float(kwargs.pop(key + "_rate", getattr(defaults, key).rate))
        los = int(kwargs.pop(key + "_los", getattr(defaults, key).days))
        kwargs[key] = [rate, los]

    return parameters_deserializer(parameters_serializer(defaults), **kwargs)


def build_csv_download(df):
    return "data:text/csv;charset=utf-8,{csv}".format(
        csv=quote(df.to_csv(index=True, encoding="utf-8"))
    )


def get_n_switch_values(input_value, elements_to_update) -> List[bool]:
    result = []
    boolean_input_value = False
    if input_value == [True]:
        boolean_input_value = True
    for _ in repeat(None, elements_to_update):
        # todo Fix once switch values make sense. Currently reported as "None" for off and "[False]" for on
        result.append(not boolean_input_value)
    return result


def prepare_visualization_group(df: DataFrame = None, **kwargs) -> List[Any]:
    """Creates plot, table and download link for data frame.
    """
    result = [{}, None, None]
    if df is not None and isinstance(df, DataFrame):
        plot_data = plot_dataframe(
            df.dropna().set_index("date").drop(columns=["day"]),
            max_y_axis=kwargs.get("max_y_axis", None),
        )

        table = (
            df_to_html_table(
                build_table(
                    df=df,
                    labels=kwargs.get("labels", df.columns),
                    modulo=kwargs.get("table_mod", 7),
                ),
                formats={
                    float: int,
                    (date, datetime): lambda d: d.strftime(DATE_FORMAT),
                },
            )
            # if kwargs.get("show_tables", None)
            # else None
        )

        csv = build_csv_download(df)
        result = [plot_data, table, csv]

    return result
