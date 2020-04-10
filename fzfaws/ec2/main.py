"""Entry point for all ec2 operations

process the raw_args passed in from __main__.py which is sys.argv[2:]
read sub command {ssh,start,stop} and route actions to appropriate functions
"""
import json
import subprocess
import argparse
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.ec2.ec2 import EC2
from fzfaws.ec2.ssh_instance import ssh_instance
from fzfaws.ec2.start_instance import start_instance
from fzfaws.ec2.stop_instance import stop_instance
from fzfaws.ec2.reboot_instance import reboot_instance
from fzfaws.ec2.terminate_instance import terminate_instance


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
        NoNameEntered: when the required name entry is empty
        NoSelectionMade: when required fzf selection is not made
    """
    parser = argparse.ArgumentParser(
        description='Perform actions on the selected instance',
        usage='faws ec2 [-h] {ssh,stop,terminate,ls,reboot} ...'
    )
    subparsers = parser.add_subparsers(dest='subparser_name')

    ssh_cmd = subparsers.add_parser(
        'ssh', description='ssh into the selected instance')
    ssh_cmd.add_argument('-p', '--path', nargs=1, action='store', default=None,
                         help='specify a different path than config for the location of the key pem file')
    ssh_cmd.add_argument('-u', '--user', nargs=1, action='store', default=['ec2-user'],
                         help='specify a different username used to ssh into the instance, default is ec2-user')
    ssh_cmd.add_argument('-A', '--bastion', action='store_true', default=False,
                         help='Add this flag when you are connecting to a bastion host using ssh forwarding')
    ssh_cmd.add_argument('-P', '--profile', nargs='?', action='store', default=False,
                         help='use a different profile, set the flag without argument to use fzf and select a profile')
    ssh_cmd.add_argument('-R', '--region', nargs='?', action='store', default=False,
                         help='use a different region, set the flag without argument to use fzf and select a region')

    start_cmd = subparsers.add_parser(
        'start', description='start the selected instance/instances')
    start_cmd.add_argument('-r', '--region', action='store_true', default=False,
                           help='select a different region rather than using the default region')
    start_cmd.add_argument('-w', '--wait', action='store_true', default=False,
                           help='pause the program and wait for the instance to be started')
    start_cmd.add_argument('-W', '--check', action='store_true', default=False,
                           help='wait until all status check have passes')
    stop_cmd = subparsers.add_parser(
        'stop', description='stop the selected instance/instances')
    stop_cmd.add_argument('-r', '--region', action='store_true', default=False,
                          help='select a different region rather than using the default region')
    stop_cmd.add_argument('-w', '--wait', action='store_true', default=False,
                          help='pause the program and wait for the instance to be started')
    stop_cmd.add_argument('-H', '--hibernate', action='store_true', default=False,
                          help='stop instance hibernate, note: will work only if your instance support hibernate stop')
    reboot_cmd = subparsers.add_parser(
        'reboot', description='reboot the selected instance/instances')
    reboot_cmd.add_argument('-r', '--region', action='store_true', default=False,
                            help='select a different region rather than using the default region')
    terminate_cmd = subparsers.add_parser(
        'terminate', description='Terminate the selected instance/instances')
    terminate_cmd.add_argument('-r', '--region', action='store_true', default=False,
                               help='select a different region rather than using the default region')
    terminate_cmd.add_argument('-w', '--wait', action='store_true', default=False,
                               help='pause the program and wait for instance to be terminated')
    ls_cmd = subparsers.add_parser(
        'ls', description='print the information of the selected instance')
    ls_cmd.add_argument('-r', '--region', action='store_true', default=False,
                        help='select a different region rather than using the default region')
    args = parser.parse_args(raw_args)

    # if no argument provided, display help message through fzf
    if not raw_args:
        available_commands = ['ssh', 'start',
                              'stop', 'terminate', 'reboot', 'ls']
        fzf = Pyfzf()
        for command in available_commands:
            fzf.append_fzf(command)
            fzf.append_fzf('\n')
        selected_command = fzf.execute_fzf(
            empty_allow=True, print_col=1, preview='faws ec2 {} -h')
        if selected_command == 'ssh':
            ssh_cmd.print_help()
        elif selected_command == 'start':
            start_cmd.print_help()
        elif selected_command == 'stop':
            stop_cmd.print_help()
        elif selected_command == 'reboot':
            reboot_cmd.print_help()
        elif selected_command == 'terminate':
            terminate_cmd.print_help()
        elif selected_command == 'ls':
            ls_cmd.print_help()
        exit()

    if args.profile == None:
        # when user set --profile flag but without argument
        args.profile = True
    if args.region == None:
        args.region = True

    if args.subparser_name == 'ssh':
        username = args.user[0]
        ssh_instance(args.profile, args.region, args.bastion, username)
    elif args.subparser_name == 'start':
        start_instance(args)
    elif args.subparser_name == 'stop':
        stop_instance(args)
    elif args.subparser_name == 'reboot':
        reboot_instance(args)
    elif args.subparser_name == 'terminate':
        terminate_instance(args)
    elif args.subparser_name == 'ls':
        ec2 = EC2()
        if args.region:
            ec2.set_ec2_region()
        ec2.set_ec2_instance(multi_select=False)
        print(json.dumps(ec2.instance, indent=4, default=str))
