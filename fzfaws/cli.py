"""Contains the fzfaws main cli entry command.

Typical usage example:
    fzfaws <command> --options
"""

import argparse
import sys

from botocore.exceptions import ClientError

from fzfaws.cloudformation.main import cloudformation
from fzfaws.ec2.main import ec2
from fzfaws.s3.main import s3
from fzfaws.utils import FileLoader, get_default_args
from fzfaws.utils.exceptions import InvalidFileType, NoSelectionMade


def main() -> None:
    """Entry function of the fzf.aws module."""
    try:
        parser = argparse.ArgumentParser(
            description="A interactive aws cli experience with the help of fzf.",
            prog="fzfaws",
        )
        subparsers = parser.add_subparsers(dest="subparser_name")
        subparsers.add_parser("cloudformation")
        subparsers.add_parser("ec2")
        subparsers.add_parser("s3")

        if len(sys.argv) < 2:
            parser.print_help()
            raise SystemExit

        args = parser.parse_args([sys.argv[1]])

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
        print("Selected file is not a valid template file type")
    except (KeyboardInterrupt, SystemExit, SystemError):
        pass
    except NoSelectionMade:
        print("No selection was made or the result was empty")
    except (ClientError, Exception) as e:
        print(e)
