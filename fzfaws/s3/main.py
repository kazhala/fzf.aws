"""main entry point for all s3 operations

process raw args passed from __main__.py and route
commands to appropriate sub functions
"""
import argparse
import json
import subprocess
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.s3.upload_s3 import upload_s3


def s3(raw_args):
    """main function for s3 operations

    Args:
        raw_args: raws args from __main__.py, starting from sys.argv[2:]
    Returns:
        None
    Raises:
        subprocess.CalledProcessError: When user exit the fzf subshell by ctrl-c
        ClientError: aws boto3 exceptions
        KeyboardInterrupt: ctrl-c during python operations
        NoNameEntered: when the required name entry is empty
        NoSelectionMade: when required fzf selection is not made
    """

    parser = argparse.ArgumentParser(description='perform CRUD operations with aws s3 bucket',
                                     usage='faws s3 [-h] {upload,download,delete,bucket,presign,ls} ...')
    subparsers = parser.add_subparsers(dest='subparser_name')
    upload_cmd = subparsers.add_parser(
        'upload', description='upload a local file/directory to s3 bucket')
    upload_cmd.add_argument('-R', '--root', action='store_true',
                            default=False, help='search local file from root directory')
    upload_cmd.add_argument('-r', '--region', action='store_true', default=False,
                            help='use a different region other than the default region')
    upload_cmd.add_argument('-p', '--path', nargs=1, action='store', default=None,
                            help='specify a s3 path (bucketName/path) using this flag and skip s3 bucket/path selection')
    args = parser.parse_args(raw_args)

    if not raw_args:
        available_commands = ['upload']
        fzf = Pyfzf()
        for command in available_commands:
            fzf.append_fzf(command)
            fzf.append_fzf('\n')
        selected_command = fzf.execute_fzf(
            empty_allow=True, print_col=1, preview='faws s3 {} -h')
        if selected_command == 'upload':
            upload_cmd.print_help()
        exit()

    if args.subparser_name == 'upload':
        upload_s3(args)
