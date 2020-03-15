"""Entry point for all ec2 operations

process the raw_args passed in from __main__.py which is sys.argv[2:]
read sub command {ssh,start,stop} and route actions to appropriate functions
"""
import json
import subprocess
import argparse
from botocore.exceptions import ClientError
from fzfaws.utils.exceptions import NoSelectionMade, NoNameEntered
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.ec2.ssh_instance import ssh_instance
from fzfaws.ec2.start_instance import start_instance


def ec2(raw_args):
    """the main function for ec2 operations

    Args:
        raw_args: raw args from the command line starting from the second position
    Returns:
        None
    Raises:
        subprocess.CalledProcessError: When user exit the fzf subshell by ctrl-c
        ClientError: aws boto3 exceptions
        KeyboardInterrupt: ctrl-c during python operations
        Exception: catch the rest
    """
    parser = argparse.ArgumentParser(
        description='Perform actions on the selected instance',
        usage='faws ec2 [-h] {ssh,stop,terminate,ls,reboot} ...'
    )
    subparsers = parser.add_subparsers(dest='subparser_name')

    ssh_cmd = subparsers.add_parser(
        'ssh', description='ssh into the selected instance')
    ssh_cmd.add_argument('-r', '--region', action='store_true', default=False,
                         help='select a different region rather than using the default region')
    ssh_cmd.add_argument('-p', '--path', nargs=1, action='store', default=None,
                         help='specify a different path than config for the location of the key pem file')
    ssh_cmd.add_argument('-u', '--user', nargs=1, action='store', default=['ec2-user'],
                         help='specify a different username used to ssh into the instance, default is ec2-user')
    start_cmd = subparsers.add_parser(
        'start', description='start the selected instance/instances')
    start_cmd.add_argument('-r', '--region', action='store_true', default=False,
                           help='select a different region rather than using the default region')
    start_cmd.add_argument('-w', '--wait', action='store_true', default=False,
                           help='pause the program and wait for the instance to be started')
    args = parser.parse_args(raw_args)

    try:
        # if no argument provided, display help message through fzf
        if not raw_args:
            available_commands = ['ssh']
            fzf = Pyfzf()
            for command in available_commands:
                fzf.append_fzf(command)
                fzf.append_fzf('\n')
            selected_command = fzf.execute_fzf(
                empty_allow=True, print_col=1, preview='faws ec2 {} -h')
            if selected_command == 'ssh':
                ssh_cmd.print_help()
            exit()

        if args.subparser_name == 'ssh':
            ssh_instance(args)
        elif args.subparser_name == 'start':
            start_instance(args)
    except subprocess.CalledProcessError as e:
        print('No selection made')
    except ClientError as e:
        print(e)
    except KeyboardInterrupt:
        print('\nExit')
    except NoSelectionMade as e:
        print(e)
    except NoNameEntered as e:
        print(e)
