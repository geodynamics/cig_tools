"""Module for creating main parser for software_dmv program.
"""

import argparse

import cli_parser.check_parser

def create_main_parser():
    """Creates main parser for the commandline interface.
    """

    parser = argparse.ArgumentParser(
        description="Where you go to get your software license.",
    )

    verbosity_group = parser.add_mutually_exclusive_group()

    verbosity_group.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const="verbose",
        dest="verbosity",
        default="",
        help="output more information about executed command",
    )
    verbosity_group.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const="quiet",
        dest="verbosity",
        default="",
        help="silence all non-error output",
    )

    subparsers = parser.add_subparsers(
        title="Commands",
        dest="command",
    )
    subparsers.required = True

    subparsers = cli_parser.check_parser.add_command(subparsers)

    parser_choose = subparsers.add_parser(
        "choose",
        help="Choose a license to insert into your project",
        description="Choose a license to insert into your project.",
    )

    parser_choose.add_argument(
        "--no-apply",
        action="store_false",
        dest="apply_choice",
        help="Write/update config file, but do not apply license to project",
    )

    parser_choose.add_argument(
        "-p",
        "--parameter",
        action="append",
        dest="parameters",
        help=("Set a license parameter. Input is in key:value form and"
              " multiple parameters can be set by using multiple flags or by"
              " concatenating key-value pairs with commas. e.g. '--parameter="
              "project:foo,author:bar'."),
    )
    parser_choose.add_argument(
        "license",
        metavar="LICENSE",
        help=("License to be created for your project. Use the 'list' command"
              " to see all supported licenses."),
    )

    parser_list = subparsers.add_parser(
        "list",
        help="List supported licenses",
        description="List supported licenses.",
    )

    parser_settings = subparsers.add_parser(
        "settings",
        help="Show current license settings for your project",
        description="Show current license settings for your project.",
    )
    parser_settings.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const="verbose",
        dest="info_level",
        default="",
        help="Show all settings and their documentation",
    )

    return parser
