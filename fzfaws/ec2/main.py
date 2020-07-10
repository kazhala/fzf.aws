"""The main entry point for all ec2 operations."""
import argparse
from typing import Any, List

from fzfaws.ec2.ls_instance import ls_instance
from fzfaws.ec2.reboot_instance import reboot_instance
from fzfaws.ec2.ssh_instance import ssh_instance
from fzfaws.ec2.start_instance import start_instance
from fzfaws.ec2.stop_instance import stop_instance
from fzfaws.ec2.terminate_instance import terminate_instance
from fzfaws.utils.pyfzf import Pyfzf


def ec2(raw_args: List[Any]) -> None:
    """Process the argument and route to proper functions.

    Process the reset of cmd argument through argparse. The first argument
    is processed through cli.py main function, the raw_args are
    sys.argv[2:].

    The raw_args from the argument already contains user default argument from
    config files, hence no process is required for user default args.

    :param raw_args: args from command line and also contains user config's default args
    :type raw_args: List[Any]
    """
    parser = argparse.ArgumentParser(
        description="Interacte with EC2 operations.", prog="fzfaws ec2",
    )
    subparsers = parser.add_subparsers(dest="subparser_name")

    ssh_cmd = subparsers.add_parser("ssh", description="ssh into the selected instance")
    ssh_cmd.add_argument(
        "-p",
        "--path",
        nargs=1,
        action="store",
        default=None,
        help="specify a different path than config for the location of the key pem file",
    )
    ssh_cmd.add_argument(
        "-u",
        "--user",
        nargs=1,
        action="store",
        default=["ec2-user"],
        help="specify a different username used to ssh into the instance, default is ec2-user",
    )
    ssh_cmd.add_argument(
        "-A",
        "--forward",
        action="store_true",
        default=False,
        help="Add this flag to enable ssh forwarding, same with ssh -A",
    )
    ssh_cmd.add_argument(
        "-t",
        "--tunnel",
        nargs="?",
        action="store",
        default=False,
        help="Use this flag to connect to a instance through ssh forwarding, "
        + "you will be making two fzf selection and then you will be directly connect to the target instance "
        + "pass in an optional parameter to specify the username to use for tunnal",
    )
    ssh_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )
    ssh_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="use a different region, set the flag without argument to use fzf and select a region",
    )

    start_cmd = subparsers.add_parser(
        "start", description="start the selected instance/instances"
    )
    start_cmd.add_argument(
        "-w",
        "--wait",
        action="store_true",
        default=False,
        help="pause the program and wait for the instance to be started",
    )
    start_cmd.add_argument(
        "-W",
        "--check",
        action="store_true",
        default=False,
        help="wait until all status check have passes",
    )
    start_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )
    start_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="use a different region, set the flag without argument to use fzf and select a region",
    )

    stop_cmd = subparsers.add_parser(
        "stop", description="stop the selected instance/instances"
    )
    stop_cmd.add_argument(
        "-w",
        "--wait",
        action="store_true",
        default=False,
        help="pause the program and wait for the instance to be started",
    )
    stop_cmd.add_argument(
        "-H",
        "--hibernate",
        action="store_true",
        default=False,
        help="stop instance hibernate, note: will work only if your instance support hibernate stop",
    )
    stop_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )
    stop_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="use a different region, set the flag without argument to use fzf and select a region",
    )

    reboot_cmd = subparsers.add_parser(
        "reboot", description="reboot the selected instance/instances"
    )
    reboot_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )
    reboot_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="use a different region, set the flag without argument to use fzf and select a region",
    )

    terminate_cmd = subparsers.add_parser(
        "terminate", description="Terminate the selected instance/instances"
    )
    terminate_cmd.add_argument(
        "-w",
        "--wait",
        action="store_true",
        default=False,
        help="pause the program and wait for instance to be terminated",
    )
    terminate_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )
    terminate_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="use a different region, set the flag without argument to use fzf and select a region",
    )

    ls_cmd = subparsers.add_parser(
        "ls", description="print the information of the selected instance"
    )
    ls_cmd.add_argument(
        "--ipv4",
        action="store_true",
        default=False,
        help="print out the selected instance ipv4 address",
    )
    ls_cmd.add_argument(
        "--privateip",
        action="store_true",
        default=False,
        help="print out the selected instance private ip address",
    )
    ls_cmd.add_argument(
        "--dns",
        action="store_true",
        default=False,
        help="print out the selected instance public dns address",
    )
    ls_cmd.add_argument(
        "--az",
        action="store_true",
        default=False,
        help="print out the selected instance availability zone",
    )
    ls_cmd.add_argument(
        "--keyname",
        action="store_true",
        default=False,
        help="print out the selected instance keyname",
    )
    ls_cmd.add_argument(
        "--instanceid",
        action="store_true",
        default=False,
        help="print out the selected instance id",
    )
    ls_cmd.add_argument(
        "-s",
        "--sg",
        action="store_true",
        default=False,
        help="print information about security groups instead of ec2 instance",
    )
    ls_cmd.add_argument(
        "--sgid",
        action="store_true",
        default=False,
        help="print out the selected security group id",
    )
    ls_cmd.add_argument(
        "--sgname",
        action="store_true",
        default=False,
        help="print out the selected security group name",
    )
    ls_cmd.add_argument(
        "-S",
        "--subnet",
        action="store_true",
        default=False,
        help="print information about subnet instead of ec2 instance",
    )
    ls_cmd.add_argument(
        "--subnetid",
        action="store_true",
        default=False,
        help="print out the selected subnet id",
    )
    ls_cmd.add_argument(
        "-v",
        "--volume",
        action="store_true",
        default=False,
        help="print information about volume instead of ec2 instance",
    )
    ls_cmd.add_argument(
        "--volumeid",
        action="store_true",
        default=False,
        help="print out the selected volume id",
    )
    ls_cmd.add_argument(
        "-V",
        "--vpc",
        action="store_true",
        default=False,
        help="print information about vpc instead of ec2 instance",
    )
    ls_cmd.add_argument(
        "--vpcid",
        action="store_true",
        default=False,
        help="print out the selected vpc id",
    )
    ls_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )
    ls_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="use a different region, set the flag without argument to use fzf and select a region",
    )
    args = parser.parse_args(raw_args)

    # if no argument provided, display help message through fzf
    if not raw_args:
        available_commands = ["ssh", "start", "stop", "terminate", "reboot", "ls"]
        fzf = Pyfzf()
        for command in available_commands:
            fzf.append_fzf(command)
            fzf.append_fzf("\n")
        selected_command = fzf.execute_fzf(
            empty_allow=True, print_col=1, preview="fzfaws ec2 {} -h"
        )
        if selected_command == "ssh":
            ssh_cmd.print_help()
        elif selected_command == "start":
            start_cmd.print_help()
        elif selected_command == "stop":
            stop_cmd.print_help()
        elif selected_command == "reboot":
            reboot_cmd.print_help()
        elif selected_command == "terminate":
            terminate_cmd.print_help()
        elif selected_command == "ls":
            ls_cmd.print_help()
        raise SystemExit

    if args.profile == None:
        # when user set --profile flag but without argument
        args.profile = True
    if args.region == None:
        args.region = True

    if args.subparser_name == "ssh":
        username = args.user[0] if args.user else "ec2-user"
        keypath = args.path[0] if args.path else ""
        if args.tunnel == None:
            args.tunnel = True
        ssh_instance(
            args.profile, args.region, args.forward, username, args.tunnel, keypath
        )
    elif args.subparser_name == "start":
        start_instance(args.profile, args.region, args.wait, args.check)
    elif args.subparser_name == "stop":
        stop_instance(args.profile, args.region, args.hibernate, args.wait)
    elif args.subparser_name == "reboot":
        reboot_instance(args.profile, args.region)
    elif args.subparser_name == "terminate":
        terminate_instance(args.profile, args.region, args.wait)
    elif args.subparser_name == "ls":
        ls_instance(
            args.profile,
            args.region,
            args.ipv4,
            args.privateip,
            args.dns,
            args.az,
            args.keyname,
            args.instanceid,
            args.sgname,
            args.sgid,
            args.subnetid,
            args.volumeid,
            args.vpcid,
            args.vpc,
            args.volume,
            args.sg,
            args.subnet,
        )
