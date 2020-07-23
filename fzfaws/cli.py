"""Contains the fzfaws main cli entry command.

Typical usage example:
    fzfaws <command> --options
"""

import argparse
import os
from pathlib import Path
from shutil import copy
import sys

from botocore.exceptions import ClientError
import pkg_resources

from fzfaws.cloudformation.main import cloudformation
from fzfaws.ec2.main import ec2
from fzfaws.s3.main import s3
from fzfaws.utils import FileLoader, get_default_args
from fzfaws.utils.exceptions import InvalidFileType, NoSelectionMade


def main() -> None:
    """Entry function of the fzf.aws module."""
    try:
        parser = argparse.ArgumentParser(
            description="An interactive aws cli experience powered by fzf.",
            prog="fzfaws",
        )
        parser.add_argument(
            "-v",
            "--version",
            action="store_true",
            default=False,
            help="display the current version",
        )
        parser.add_argument(
            "--copy-config",
            dest="copy_config",
            action="store_true",
            default=False,
            help="copy the configuration file to $XDG_CONFIG_HOME/fzfaws/ or $HOME/.config/fzfaws/",
        )
        subparsers = parser.add_subparsers(dest="subparser_name")
        subparsers.add_parser("cloudformation")
        subparsers.add_parser("ec2")
        subparsers.add_parser("s3")

        if len(sys.argv) < 2:
            parser.print_help()
            sys.exit(1)

        args = parser.parse_args([sys.argv[1]])

        if args.copy_config:
            copy_config()
            sys.exit(0)
        elif args.version:
            version = pkg_resources.require("fzfaws")[0].version
            print("Current fzfaws version: %s" % version)
            sys.exit(0)

        fileloader = FileLoader()
        fileloader.load_config_file()

        argument_list = get_default_args(args.subparser_name, sys.argv[2:])

        if args.subparser_name == "cloudformation":
            cloudformation(argument_list)
        elif args.subparser_name == "ec2":
            ec2(argument_list)
        elif args.subparser_name == "s3":
            s3(argument_list)

    except InvalidFileType:
        print("Selected file is not a valid file type")
        sys.exit(1)
    except SystemExit:
        raise
    except (KeyboardInterrupt, SystemError):
        sys.exit(1)
    except NoSelectionMade:
        print("No selection was made or the result was empty")
        sys.exit(1)
    except (ClientError, Exception) as e:
        print(e)
        sys.exit(1)


def copy_config() -> None:
    """Copy the default fzfaws.yml to $XDG_CONFIG_HOME/fzfaws/."""
    default_config_path = Path(__file__).resolve().parent.joinpath("./fzfaws.yml")
    destination_config_path = "%s/fzfaws/" % os.getenv(
        "XDG_CONFIG_HOME", str(Path.home())
    )
    if not Path(destination_config_path).is_dir():
        Path(destination_config_path).mkdir(parents=True, exist_ok=True)
    copy(default_config_path, destination_config_path)
