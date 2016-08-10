"""This file provides functionality for using the license repository included
 in the software_dmv project.
"""

import json
import os
import re


LICENSE_DIR = "Licenses"

DEFAULT_LICENSE = "generic"

LICENSE_EXT = "txt"
LICENSE_HEADER_SUFFIX = "_header"


def get_license_list():
    return sorted({
        os.path.basename(path).rstrip(LICENSE_HEADER_SUFFIX)
        for dirpath, dirnames, filenames in os.walk(LICENSE_DIR)
        for filename in filenames
        for path, ext in [os.path.splitext(filename)]
    })


def get_license_info(license_name):
    license_txtfile = open(
        os.path.join(LICENSE_DIR, license_name + LICENSE_EXT),
        "rt",
    )
    license_json = json.load(
        open(
            os.path.join(LICENSE_DIR, license_name + ".json"),
            "rt",
        )
    )

    try:
        header_txtfile = open(
            os.path.join(LICENSE_DIR, license_name + "_header.txt"),
            "rt",
        )
    except FileNotFoundError:
        header_txtfile = open(
            os.path.join(LICENSE_DIR, DEFAULT_LICENSE + LICENSE_HEADER_SUFFIX),
            "rt",
        )

    license_json["fullText"] = str(license_txtfile)
    license_json["headerText"] = str(header_txtfile)

    return license_json


def format_header(header, path, config):
    """Headers use double curly braces to describe required inputs.
    Inside a set of curly braces is the name of the input.
    """
    pattern = re.compile(r"{{\s*([^\s]+)\s*}}")
    match = pattern.search(header)
    formatted_header = ""

    while match:
        begin, end = match.span()
        input_name = match.groups()

        formatted_header += (match.string[:begin]
            + str(config["LicenseParameters"][input_name])
        )

        match = pattern.search(match.string[end:])

    formatted_header += match.string[end:]

    return formatted_header