"""Contains the entry point for all lambda operations."""
from typing import List, Any
import argparse
import sys
from fzfaws.lambdaf.invoke_function import invoke_function


def lambdaf(raw_args: List[Any]) -> None:
    """Parse arguments and direct traffic to lambda handler, internal use only.

    The raw_args are the processed args through cli.py main function.
    It also already contains the user default args so no need to process
    default args anymore.

    :param raw_args: list of args to be parsed
    :type raw_args: list
    """
    parser = argparse.ArgumentParser(
        prog="fzfaws lambda",
        description="Perform operations and interact with aws Lambda.",
    )
    subparsers = parser.add_subparsers(dest="subparser_name")

    invoke_cmd = subparsers.add_parser(
        "invoke", description="Invoke lambda function synchronously."
    )
    invoke_cmd.add_argument(
        "-p",
        "--payload",
        action="store",
        nargs="?",
        default=False,
        help="specify a json file to provide to lambda as input",
    )
    invoke_cmd.add_argument(
        "-r",
        "--root",
        action="store_true",
        default=False,
        help="search file from home directory when using --payload flag",
    )
    invoke_cmd.add_argument(
        "-A",
        "--all",
        action="store_true",
        default=False,
        help="list all versions and functions",
    )
    invoke_cmd.add_argument(
        "-a",
        "--async",
        action="store_true",
        default=False,
        dest="asynk",
        help="invoke function asynchronously",
    )
    invoke_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a region for the operation",
    )
    invoke_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a profile for the operation",
    )

    args = parser.parse_args(raw_args)

    if not raw_args:
        parser.print_help()
        sys.exit(0)

    if args.profile == None:
        args.profile = True
    if args.region == None:
        args.region = True

    if args.subparser_name == "invoke":
        if args.payload == None:
            args.payload = True
        invoke_function(
            args.profile, args.region, args.asynk, args.all, args.payload, args.root
        )
