""" Main entry point of the program.

Typical usage example:
    faws <command> --options
"""
import sys
from botocore.exceptions import ClientError
from fzfaws.utils.exceptions import (
    NoCommandFound,
    NoSelectionMade,
    InvalidFileType,
)
from fzfaws.cloudformation.main import cloudformation
from fzfaws.ec2.main import ec2
from fzfaws.s3.main import s3
from fzfaws.utils import FileLoader, get_default_args


def main():
    """Entry function of the fzf.aws module"""

    try:
        if len(sys.argv) < 2:
            raise NoCommandFound()
        available_routes = ["cloudformation", "ec2", "s3"]
        action_command = sys.argv[1]
        if action_command not in available_routes:
            raise NoCommandFound()
        fileloader = FileLoader()
        fileloader.load_config_file()

        argument_list = get_default_args(action_command, sys.argv[2:])

        if action_command == "cloudformation":
            cloudformation(argument_list)
        elif action_command == "ec2":
            ec2(argument_list)
        elif action_command == "s3":
            s3(argument_list)

    # display help message
    # did'n use argparse at the entry level thus creating similar help message
    except NoCommandFound as e:
        print("usage: faws [-h] {cloudformation, ec2, keypair, s3} ...\n")
        print("A better aws cli experience with the help of fzf\n")
        print("positional arguments:")
        print("  {cloudformation,ec2,keypair,s3}\n")
        print("optional arguments:")
        print("  -h, --help            show this help message and exit")
    except InvalidFileType:
        print("Selected file is not a valid template file type")
        print("Exiting..")
    except (KeyboardInterrupt, SystemExit, SystemError):
        print("Exit")
    except NoSelectionMade:
        print("No selection was made")
        print("Exit..")
    except (ClientError, Exception) as e:
        print(e)


if __name__ == "__main__":
    main()
