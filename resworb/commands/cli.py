#! /usr/bin/env python

import argparse
import logging
import os
from typing import Optional, Type

from resworb.browsers.safari import Safari
from resworb.exporter import JSONExporter, PickleExporter, TOMLExporter, YAMLExporter
from resworb.formatter import WeixinFormatter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_FORMATTERS = [
    WeixinFormatter(),
]

EXPORT_FACTORY = {
    ".yml": YAMLExporter,
    ".yaml": YAMLExporter,
    ".toml": TOMLExporter,
    ".json": JSONExporter,
    ".pkl": PickleExporter,
    ".pickle": PickleExporter,
}


def library_path() -> Optional[str]:
    home = os.getenv("HOME")
    if not home:
        return None

    path = os.path.join(home, "Library", "Safari")

    return path


def add_export_arguments(parser):
    parser.add_argument(
        "-b",
        "--browser",
        type=str,
        required=True,
        help="Seleted browser.",
    )

    sources = [
        "opened_tabs",
        "cloud_tabs",
        "readings",
        "bookmarks",
        "histories",
    ]
    parser.add_argument(
        "-s",
        "--source",
        type=str,
        nargs="+",
        choices=sources,
        default=None,
        help="If not given, export all sources.",
    )
    parser.add_argument(
        "-t",
        "--target",
        type=str,
        required=True,
        help="Output file name.",
    )

    library = library_path()
    parser.add_argument(
        "-l",
        "--library",
        type=str,
        default=library,
        help=f"Library location (default: {library!r})",
    )

    return parser


def parse_args():
    # pylint: disable=redefined-outer-name
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(required=True)
    export_parser = subparsers.add_parser("export", help="Export browser data")
    add_export_arguments(export_parser)

    args = parser.parse_args()

    if not args.source:
        args.source = "all"

    return args


def format_records(records, formatters):
    def _format(record):
        for f in formatters:
            record = f(record)

        return record

    results = {}
    for key, value in records.items():
        if key == "cloud_tabs":
            results[key] = [
                {
                    k: list(map(_format, v)) if k == "tabs" else v
                    for k, v in device_value.items()
                }
                for device_value in value
            ]
        else:
            results[key] = list(map(_format, value))

    return results


def get_browser_class(name) -> Type:
    if name == "safari":
        return Safari

    msg = "Unsupported browser: {name}"
    raise ValueError(msg)


def get_exporter(filename) -> Type:
    file_type = os.path.splitext(filename)[1]
    exporter_class = EXPORT_FACTORY.get(file_type)
    if exporter_class is None:
        msg = f"Unsupported file type: {file_type}"
        raise ValueError(msg)

    return exporter_class()


def main():
    args = parse_args()

    browser_class = get_browser_class(args.browser)
    browser = browser_class(library=args.library)

    records = browser.export(args.source)
    records = format_records(records, DEFAULT_FORMATTERS)

    exporter = get_exporter(args.target)
    exporter.export_to_file(records, args.target)

    logger.info("Export statistics:")
    for source, data in records.items():
        if source == "cloud_tabs":
            logger.info("%s\t%d", source, sum(len(x["tabs"]) for x in data))
        else:
            logger.info("%s\t%d", source, len(data))
