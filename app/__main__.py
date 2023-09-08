from argparse import ArgumentParser
from typing import Any, Mapping

from lxml import etree

import app
from app.core import AppData, Transport
from app.lib import Pipeline
from app.use_cases.main_pipeline import (
    AppDataToJson,
    FetchForms,
    BQueryLabels,
)
from app.utils import import_string


# =============================================================================
# HELPERS
# =============================================================================

def _init_transport_from_config(config: Mapping[str, Any]) -> Transport:
    # TODO: Nope. Revisit this. An abstract factory would work well here.
    #  This assumes that only a http transport is available.
    transport_klass = import_string(config["main_pipeline"]["transport"])
    http_transport_config = config["http_transport"]
    transport_adapter = import_string(
        http_transport_config["transport_adapter"]
    )
    connect_timeout = http_transport_config.get("connect_timeout")
    read_timeout = http_transport_config.get("read_timeout")
    transport_adapter_kwargs = http_transport_config["transport_adapter_kwargs"]
    transport = transport_klass(
        transport_adapter=transport_adapter(**transport_adapter_kwargs),
        connect_timeout=connect_timeout,
        read_timeout=read_timeout
    )
    return transport


def argparse_factory(prog_name: str = "rich_xforms_subs") -> ArgumentParser:
    """
    Returns a new ArgumentParser instance configured for use with this program.

    :param prog_name: An optional name to be used as the program name.
    :return: An ArgumentParser instance for use with this program.
    """

    parser = ArgumentParser(
        prog=prog_name,
        description=(
            "An ETL tool used to process XForms submissions including "
            "enriching the submissions by adding the original question labels "
            "to the submissions and serializing the final result into an easy "
            "to consume format."
        ),
        epilog="Let's go ;-)"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help=(
            "The location of the application config file. Only yaml files are "
            "supported currently (default: %(default)s)."
        ),
        type=str
    )
    parser.add_argument(
        "-o",
        "--out_dir",
        default="out",
        help=(
            "The output directory where generated xls-forms are persisted "
            "(default: %(default)s)."
        ),
        type=str
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Disable printers from producing any output on std out."
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help=(
            "The level of output that printers should produce "
            "(default: %(default)d)."
        )
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )

    return parser


def read_form_xls_file(form_source: str) -> etree._ElementTree:  # type: ignore
    return etree.parse(form_source)


def main_pipeline_factory(out_dir: str) -> Pipeline[AppData, Any]:
    config: Mapping[str, Any] = app.config
    transport = _init_transport_from_config(config)
    return Pipeline(
        FetchForms(transport=transport),
        AppDataToJson(file_path="%s/%s" % (out_dir, "all_forms.json")),
        BQueryLabels(out_dir=out_dir),
    )


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    parser = argparse_factory()
    args = parser.parse_args()

    app.setup(config_file_path=args.config)
    app_data = AppData()
    main_pipeline: Pipeline[AppData, Any] = main_pipeline_factory(
        out_dir=args.out_dir
    )
    main_pipeline.execute(app_data)
    print("Done...")


if __name__ == "__main__":
    main()
