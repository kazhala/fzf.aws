"""Contains the main entry point for all cloudformation operations."""
import argparse
import sys
from typing import Any, List

from fzfaws.cloudformation.changeset_stack import changeset_stack
from fzfaws.cloudformation.create_stack import create_stack
from fzfaws.cloudformation.delete_stack import delete_stack
from fzfaws.cloudformation.drift_stack import drift_stack
from fzfaws.cloudformation.ls_stack import ls_stack
from fzfaws.cloudformation.update_stack import update_stack
from fzfaws.cloudformation.validate_stack import validate_stack
from fzfaws.utils.pyfzf import Pyfzf


def cloudformation(raw_args: List[Any]) -> None:
    """Parse arguments and direct traffic to handler, internal use only.

    The raw_args are the processed args through cli.py main function.
    It also already contains the user default args so no need to process
    default args anymore.

    :param raw_args: list of args to be parsed
    :type raw_args: list
    """
    parser = argparse.ArgumentParser(
        description="Perform operations and interact with aws CloudFormation.",
        prog="fzfaws cloudformation",
    )
    subparsers = parser.add_subparsers(dest="subparser_name")

    update_cmd = subparsers.add_parser(
        "update", description="Perform update on an existing stack."
    )
    update_cmd.add_argument(
        "-b",
        "--bucket",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/) and skip s3 bucket/path selection",
    )
    update_cmd.add_argument(
        "-v",
        "--version",
        nargs="?",
        action="store",
        default=False,
        help="choose a version of the template in s3 bucket",
    )
    update_cmd.add_argument(
        "-r",
        "--root",
        action="store_true",
        default=False,
        help="search local files from root",
    )
    update_cmd.add_argument(
        "-l",
        "--local",
        nargs="?",
        action="store",
        default=False,
        help="update the stack using template in local machine",
    )
    update_cmd.add_argument(
        "-x",
        "--replace",
        action="store_true",
        default=False,
        help="perform replacing update, replace the stack with a new template",
    )
    update_cmd.add_argument(
        "-w",
        "--wait",
        action="store_true",
        default=False,
        help="wait for stack to finish update",
    )
    update_cmd.add_argument(
        "-E",
        "--extra",
        action="store_true",
        default=False,
        help="configure extra settings during update stack (E.g.Tags, iam role, notification, policy etc)",
    )
    update_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a profile for the operation",
    )
    update_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a region for the operation",
    )

    create_cmd = subparsers.add_parser("create", description="Create a new stack.")
    create_cmd.add_argument(
        "-b",
        "--bucket",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/) and skip s3 bucket/path selection",
    )
    create_cmd.add_argument(
        "-v",
        "--version",
        nargs="?",
        action="store",
        default=False,
        help="choose a version of the template in s3 bucket",
    )
    create_cmd.add_argument(
        "-r",
        "--root",
        action="store_true",
        default=False,
        help="search local files from root",
    )
    create_cmd.add_argument(
        "-l",
        "--local",
        nargs="?",
        action="store",
        default=False,
        help="create stack using template in local machine",
    )
    create_cmd.add_argument(
        "-w",
        "--wait",
        action="store_true",
        default=False,
        help="wait for the stack to finish create",
    )
    create_cmd.add_argument(
        "-E",
        "--extra",
        action="store_true",
        default=False,
        help="configure extra settings during create stack (E.g.Tags, iam role, notification, policy etc)",
    )
    create_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a profile for the operation",
    )
    create_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a region for the operation",
    )

    delete_cmd = subparsers.add_parser(
        "delete", description="Delete an existing stack."
    )
    delete_cmd.add_argument(
        "-i",
        "--iam",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a iam arn that has the permission to delete the current stack",
    )
    delete_cmd.add_argument(
        "-w",
        "--wait",
        action="store_true",
        default=False,
        help="wait for the stack to be deleted",
    )
    delete_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a profile for the operation",
    )
    delete_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a region for the operation",
    )

    ls_cmd = subparsers.add_parser(
        "ls", description="Display infomation of the selcted stack."
    )
    ls_cmd.add_argument(
        "-r",
        "--resource",
        action="store_true",
        default=False,
        help="display information on stack resources",
    )
    ls_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a profile for the operation",
    )
    ls_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a region for the operation",
    )
    ls_cmd.add_argument(
        "--tag",
        action="store_true",
        default=False,
        help="display tag of the selected stack",
    )
    ls_cmd.add_argument(
        "--arn",
        action="store_true",
        default=False,
        help="display arn of the selected stack",
    )
    ls_cmd.add_argument(
        "--name",
        action="store_true",
        default=False,
        help="display name of the selected stack",
    )
    ls_cmd.add_argument(
        "--type",
        action="store_true",
        default=False,
        help="display the type of the selected stack resource",
    )

    drift_cmd = subparsers.add_parser(
        "drift", description="Detect drift on stack/resources."
    )
    drift_cmd.add_argument(
        "-i",
        "--info",
        action="store_true",
        default=False,
        help="check the current drift status",
    )
    drift_cmd.add_argument(
        "-s",
        "--select",
        action="store_true",
        default=False,
        help="select individual resources to detect drift",
    )
    drift_cmd.add_argument(
        "-w",
        "--wait",
        action="store_true",
        default=False,
        help="wait for the drift detection result",
    )
    drift_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a profile for the operation",
    )
    drift_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a region for the operation",
    )

    changeset_cmd = subparsers.add_parser(
        "changeset", description="Create a change set for the selected stack."
    )
    changeset_cmd.add_argument(
        "-b",
        "--bucket",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/) and skip s3 bucket/path selection",
    )
    changeset_cmd.add_argument(
        "-v",
        "--version",
        nargs="?",
        action="store",
        default=False,
        help="choose a version of the template in s3 bucket",
    )
    changeset_cmd.add_argument(
        "-r",
        "--root",
        action="store_true",
        default=False,
        help="search local files from root",
    )
    changeset_cmd.add_argument(
        "-l",
        "--local",
        action="store_true",
        default=False,
        help="create the changeset using template in local machine",
    )
    changeset_cmd.add_argument(
        "-w",
        "--wait",
        action="store_true",
        default=False,
        help="wait for the changeset to finish create",
    )
    changeset_cmd.add_argument(
        "-x",
        "--replace",
        action="store_true",
        default=False,
        help="perform replacing changeset, replace the current template with a new template and create the changeset",
    )
    changeset_cmd.add_argument(
        "-i", "--info", action="store_true", help="view the result of the changeset"
    )
    changeset_cmd.add_argument(
        "-e",
        "--execute",
        action="store_true",
        help="execute update based on the selected changeset",
    )
    changeset_cmd.add_argument(
        "-d", "--delete", action="store_true", help="delete the selected changeset"
    )
    changeset_cmd.add_argument(
        "-E",
        "--extra",
        action="store_true",
        default=False,
        help="configure extra settings during creating a changeset (E.g.Tags, iam role, notification, policy etc)",
    )
    changeset_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a profile for the operation",
    )
    changeset_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a region for the operation",
    )

    validate_cmd = subparsers.add_parser(
        "validate",
        description="Validate the selected template.",
    )
    validate_cmd.add_argument(
        "-b",
        "--bucket",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/) and skip s3 bucket/path selection",
    )
    validate_cmd.add_argument(
        "-l",
        "--local",
        nargs="?",
        action="store",
        default=False,
        help="validate template in local machine",
    )
    validate_cmd.add_argument(
        "-r",
        "--root",
        action="store_true",
        default=False,
        help="search files from root",
    )
    validate_cmd.add_argument(
        "-v",
        "--version",
        nargs="?",
        default=False,
        help="choose a version of the template in s3 bucket",
    )
    validate_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a profile for the operation",
    )
    validate_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a region for the operation",
    )
    args = parser.parse_args(raw_args)

    # if no argument provided, display help message through fzf
    if not raw_args:
        available_commands = [
            "update",
            "create",
            "delete",
            "ls",
            "drift",
            "changeset",
            "validate",
        ]
        fzf = Pyfzf()
        for command in available_commands:
            fzf.append_fzf("%s\n" % command)
        selected_command = fzf.execute_fzf(
            empty_allow=True, print_col=1, preview="fzfaws cloudformation {} -h"
        )
        if selected_command == "update":
            update_cmd.print_help()
        elif selected_command == "create":
            create_cmd.print_help()
        elif selected_command == "delete":
            delete_cmd.print_help()
        elif selected_command == "ls":
            ls_cmd.print_help()
        elif selected_command == "drift":
            drift_cmd.print_help()
        elif selected_command == "changeset":
            changeset_cmd.print_help()
        elif selected_command == "validate":
            changeset_cmd.print_help()
        sys.exit(0)

    # when user set --profile/region flag but without argument
    # argparse will have a None value instead of default value False
    # convert to True for better processing
    if args.profile == None:
        args.profile = True
    if args.region == None:
        args.region = True
    if hasattr(args, "local") and args.local == None:
        args.local = True
    if hasattr(args, "bucket"):
        args.bucket = args.bucket[0] if args.bucket else None
    if hasattr(args, "version") and args.version == None:
        args.version = True

    if args.subparser_name == "create":
        create_stack(
            args.profile,
            args.region,
            args.local,
            args.root,
            args.wait,
            args.extra,
            args.bucket,
            args.version,
        )
    elif args.subparser_name == "update":
        update_stack(
            args.profile,
            args.region,
            args.replace,
            args.local,
            args.root,
            args.wait,
            args.extra,
            args.bucket,
            args.version,
        )
    elif args.subparser_name == "delete":
        if args.iam == None:
            args.iam = True
        delete_stack(args.profile, args.region, args.wait, args.iam)
    elif args.subparser_name == "ls":
        ls_stack(
            args.profile,
            args.region,
            args.resource,
            args.name,
            args.arn,
            args.tag,
            args.type,
        )
    elif args.subparser_name == "drift":
        drift_stack(args.profile, args.region, args.info, args.select, args.wait)
    elif args.subparser_name == "changeset":
        changeset_stack(
            args.profile,
            args.region,
            args.replace,
            args.local,
            args.root,
            args.wait,
            args.info,
            args.execute,
            args.delete,
            args.extra,
            args.bucket,
            args.version,
        )
    elif args.subparser_name == "validate":
        validate_stack(
            args.profile, args.region, args.local, args.root, args.bucket, args.version
        )
