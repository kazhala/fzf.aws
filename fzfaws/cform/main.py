"""Entry point for all cloudformaiton operations

process the raw_args passed in from __main__.py which is sys.argv[2:]
read sub command {update,create,delete,drift,changeset} and route
actions to appropriate functions
"""
import boto3
import json
import subprocess
import argparse
import sys
from botocore.exceptions import ClientError
from fzfaws.cform.delete_stack import delete_stack
from fzfaws.cform.update_stack import update_stack
from fzfaws.cform.helper.get_stack import get_stack
from fzfaws.cform.create_stack import create_stack
from fzfaws.cform.drift_stack import drift_stack
from fzfaws.cform.changeset_stack import changeset_stack
from fzfaws.utils.pyfzf import Pyfzf


def cform(raw_args):
    """Entry of cloudformation operations

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
        description='CRUD operation on aws cloudformation.',
        usage='faws cform [-h] {update,create,delete,drift,changeset} ...'
    )
    subparsers = parser.add_subparsers(dest='subparser_name')
    # sub commands
    update_cmd = subparsers.add_parser(
        'update', description='update an existing stack')
    update_cmd.add_argument('-t', '--tag', action='store_true',
                            default=False, help='update the tag during update')
    update_cmd.add_argument('-R', '--root', action='store_true', default=False,
                            help='search local file from root instead of current directory')
    update_cmd.add_argument('-p', '--path', nargs=1, action='store', default=None,
                            help='specifie a path where the local file is stored')
    update_cmd.add_argument('-l', '--local', action='store_true',
                            default=False, help='upload local file')
    update_cmd.add_argument('-r', '--replace', action='store_true', default=False,
                            help='replace current template to update')
    update_cmd.add_argument('-w', '--wait', action='store_true', default=False,
                            help='Pause the script and wait for update complete signal, max wait time 60mins')
    update_cmd.add_argument('-c', '--capabilities', action='store_true', default=False,
                            help='Select capabilities to acknowledge during stack update')

    create_cmd = subparsers.add_parser(
        'create', description='create a new stack')
    create_cmd.add_argument('-R', '--root', action='store_true', default=False,
                            help='search local file from root instead of current directory')
    create_cmd.add_argument('-p', '--path', nargs=1, action='store', default=None,
                            help='specifie a path where the local file is stored')
    create_cmd.add_argument('-l', '--local', action='store_true',
                            default=False, help='upload local file')
    create_cmd.add_argument('-w', '--wait', action='store_true', default=False,
                            help='Pause the script and wait for create complete signal, max wait time 60mins')
    create_cmd.add_argument('-c', '--capabilities', action='store_true', default=False,
                            help='Select capabilities to acknowledge during stack creation')

    delete_cmd = subparsers.add_parser(
        'delete', description='delete an existing stack')
    delete_cmd.add_argument('-w', '--wait', action='store_true', default=False,
                            help='Pause the script and wait for delete complete signal, max wait time 60mins')
    ls_cmd = subparsers.add_parser(
        'ls', description='list and print infomation of the selcted stack')
    drift_cmd = subparsers.add_parser(
        'drift', description='drift detection on the stack/resources')
    drift_cmd.add_argument('-i', '--info', action='store_true', default=False,
                           help='Check the current drift status')
    drift_cmd.add_argument('-s', '--select', action='store_true', default=False,
                           help='select individual resource or resources to detect drift')

    changeset_cmd = subparsers.add_parser(
        'changeset', description='create a change set for the selected stack')
    changeset_cmd.add_argument('-R', '--root', action='store_true', default=False,
                               help='search local file from root instead of current directory')
    changeset_cmd.add_argument('-p', '--path', nargs=1, action='store', default=None,
                               help='specifie a path where the local file is stored')
    changeset_cmd.add_argument('-l', '--local', action='store_true',
                               default=False, help='upload local file')
    changeset_cmd.add_argument('-w', '--wait', action='store_true', default=False,
                               help='Pause the script and wait for create complete signal, max wait time 60mins')
    changeset_cmd.add_argument('-c', '--capabilities', action='store_true', default=False,
                               help='Select capabilities to acknowledge during stack creation')
    changeset_cmd.add_argument('-t', '--tag', action='store_true',
                               default=False, help='update the tag during update')
    changeset_cmd.add_argument('-r', '--replace', action='store_true', default=False,
                               help='replace current template to update')
    changeset_cmd.add_argument('-i', '--info', action='store_true',
                               help='view the result of the changeset')
    changeset_cmd.add_argument('-e', '--execute', action='store_true',
                               help='Execute update based on selected changeset')
    args = parser.parse_args(raw_args)

    try:
        # if no argument provided, display help message through fzf
        if not raw_args:
            available_commands = ['update', 'create',
                                  'delete', 'ls', 'drift', 'changeset']
            fzf = Pyfzf()
            for command in available_commands:
                fzf.append_fzf(command)
                fzf.append_fzf('\n')
            selected_command = fzf.execute_fzf(
                empty_allow=True, print_col=1, preview='faws cform {} -h')
            if selected_command == 'update':
                update_cmd.print_help()
            elif selected_command == 'create':
                create_cmd.print_help()
            elif selected_command == 'delete':
                delete_cmd.print_help()
            elif selected_command == 'ls':
                ls_cmd.print_help()
            elif selected_command == 'drift':
                drift_cmd.print_help()
            elif selected_command == 'changeset':
                changeset_cmd.print_help()
            exit()

        if args.subparser_name == 'create':
            create_stack(args)

        else:
            # get the selected_stack {'StackName': str, 'StackDetails': {}}
            selected_stack = get_stack()
            if args.subparser_name == 'update':
                update_stack(
                    args, selected_stack['StackName'], selected_stack['StackDetails'])
            elif args.subparser_name == 'delete':
                delete_stack(args, selected_stack['StackName'],
                             selected_stack['StackDetails'])
            elif args.subparser_name == 'ls':
                print(json.dumps(
                    selected_stack['StackDetails'], indent=4, default=str))
            elif args.subparser_name == 'drift':
                drift_stack(
                    args, selected_stack['StackName'], selected_stack['StackDetails'])
            elif args.subparser_name == 'changeset':
                changeset_stack(
                    args, selected_stack['StackName'], selected_stack['StackDetails'])

    except subprocess.CalledProcessError as e:
        print('No selection made')
    except ClientError as e:
        print(e)
    except KeyboardInterrupt:
        print('\nExit')
    except Exception as e:
        print(e)
