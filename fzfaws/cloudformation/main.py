"""Contains the main entry point for all cloudformation operations."""
import argparse

from fzfaws.cloudformation.changeset_stack import changeset_stack
from fzfaws.cloudformation.create_stack import create_stack
from fzfaws.cloudformation.delete_stack import delete_stack
from fzfaws.cloudformation.drift_stack import drift_stack
from fzfaws.cloudformation.ls_stack import ls_stack
from fzfaws.cloudformation.update_stack import update_stack
from fzfaws.cloudformation.validate_stack import validate_stack
from fzfaws.utils.pyfzf import Pyfzf


def cloudformation(raw_args: list) -> None:
    """Parse arguments and direct traffic to handler, internal use only.

    The raw_args are the processed args through cli.py main function.
    It also already contains the user default args so no need to process
    default args anymore.

    :param raw_args: list of args to be parsed
    :type raw_args: list
    """
    parser = argparse.ArgumentParser(
        description="CRUD operation on aws cloudformation.",
        usage="faws cloudformation [-h] {update,create,delete,drift,changeset} ...",
    )
    subparsers = parser.add_subparsers(dest="subparser_name")

    update_cmd = subparsers.add_parser("update", description="update an existing stack")
    update_cmd.add_argument(
        "-b",
        "--bucket",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/)"
        + "using this flag and skip s3 bucket/path selection",
    )
    update_cmd.add_argument(
        "-v",
        "--version",
        nargs="?",
        action="store",
        default=False,
        help="use a previous version of the template in s3 bucket",
    )
    update_cmd.add_argument(
        "-r",
        "--root",
        action="store_true",
        default=False,
        help="search local file from root instead of current directory",
    )
    update_cmd.add_argument(
        "-l",
        "--local",
        nargs="?",
        action="store",
        default=False,
        help="upload local file",
    )
    update_cmd.add_argument(
        "-x",
        "--replace",
        action="store_true",
        default=False,
        help="replace current template to update",
    )
    update_cmd.add_argument(
        "-w",
        "--wait",
        action="store_true",
        default=False,
        help="Pause the script and wait for update complete signal, max wait time 60mins",
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
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )
    update_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="use a different region, set the flag without argument to use fzf and select a region",
    )

    create_cmd = subparsers.add_parser("create", description="create a new stack")
    create_cmd.add_argument(
        "-b",
        "--bucket",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/)"
        + "using this flag and skip s3 bucket/path selection",
    )
    create_cmd.add_argument(
        "-v",
        "--version",
        nargs="?",
        action="store",
        default=False,
        help="use a previous version of the template in s3 bucket",
    )
    create_cmd.add_argument(
        "-r",
        "--root",
        action="store_true",
        default=False,
        help="search local file from root instead of current directory",
    )
    create_cmd.add_argument(
        "-l",
        "--local",
        nargs="?",
        action="store",
        default=False,
        help="upload local file",
    )
    create_cmd.add_argument(
        "-w",
        "--wait",
        action="store_true",
        default=False,
        help="Pause the script and wait for create complete signal, max wait time 60mins",
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
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )
    create_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="use a different region, set the flag without argument to use fzf and select a region",
    )

    delete_cmd = subparsers.add_parser("delete", description="delete an existing stack")
    delete_cmd.add_argument(
        "-i",
        "--iam",
        nargs="?",
        action="store",
        default=False,
        help="specify a iam arn that has the permission to delete the current stack",
    )
    delete_cmd.add_argument(
        "-w",
        "--wait",
        action="store_true",
        default=False,
        help="Pause the script and wait for delete complete signal, max wait time 60mins",
    )
    delete_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )
    delete_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="use a different region, set the flag without argument to use fzf and select a region",
    )

    ls_cmd = subparsers.add_parser(
        "ls", description="list and print infomation of the selcted stack"
    )
    ls_cmd.add_argument(
        "-r",
        "--resource",
        action="store_true",
        default=False,
        help="display information on resources",
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
    ls_cmd.add_argument(
        "--tag",
        action="store_true",
        default=False,
        help="print tag of the stack instead of the entire stack details",
    )
    ls_cmd.add_argument(
        "--arn",
        action="store_true",
        default=False,
        help="print arn of the stack instead of the entire stack details",
    )
    ls_cmd.add_argument(
        "--name",
        action="store_true",
        default=False,
        help="print name of the stack or stack resource instead of the entire details",
    )
    ls_cmd.add_argument(
        "--type",
        action="store_true",
        default=False,
        help="print the type of the stack resource instead of the entire resource details",
    )

    drift_cmd = subparsers.add_parser(
        "drift", description="drift detection on the stack/resources"
    )
    drift_cmd.add_argument(
        "-i",
        "--info",
        action="store_true",
        default=False,
        help="Check the current drift status",
    )
    drift_cmd.add_argument(
        "-s",
        "--select",
        action="store_true",
        default=False,
        help="select individual resource or resources to detect drift",
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
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )
    drift_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="use a different region, set the flag without argument to use fzf and select a region",
    )

    changeset_cmd = subparsers.add_parser(
        "changeset", description="create a change set for the selected stack"
    )
    changeset_cmd.add_argument(
        "-b",
        "--bucket",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/)"
        + "using this flag and skip s3 bucket/path selection",
    )
    changeset_cmd.add_argument(
        "-v",
        "--version",
        nargs="?",
        action="store",
        default=False,
        help="use a previous version of the template in s3 bucket",
    )
    changeset_cmd.add_argument(
        "-r",
        "--root",
        action="store_true",
        default=False,
        help="search local file from root instead of current directory",
    )
    changeset_cmd.add_argument(
        "-l", "--local", action="store_true", default=False, help="upload local file"
    )
    changeset_cmd.add_argument(
        "-w",
        "--wait",
        action="store_true",
        default=False,
        help="Pause the script and wait for create complete signal, max wait time 60mins",
    )
    changeset_cmd.add_argument(
        "-x",
        "--replace",
        action="store_true",
        default=False,
        help="replace current template to update",
    )
    changeset_cmd.add_argument(
        "-i", "--info", action="store_true", help="view the result of the changeset"
    )
    changeset_cmd.add_argument(
        "-e",
        "--execute",
        action="store_true",
        help="Execute update based on selected changeset",
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
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )
    changeset_cmd.add_argument(
        "-R",
        "--region",
        nargs="?",
        action="store",
        default=False,
        help="use a different region, set the flag without argument to use fzf and select a region",
    )

    validate_cmd = subparsers.add_parser(
        "validate",
        description="validate the selected template, by default, search a template through s3",
    )
    validate_cmd.add_argument(
        "-b",
        "--bucket",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/)"
        + "using this flag and skip s3 bucket/path selection",
    )
    validate_cmd.add_argument(
        "-l",
        "--local",
        nargs="?",
        action="store",
        default=False,
        help="upload local file",
    )
    validate_cmd.add_argument(
        "-r", "--root", action="store_true", default=False, help="search file from root"
    )
    validate_cmd.add_argument(
        "-v",
        "--version",
        nargs="?",
        default=False,
        help="use previous versions of the cloudformation template",
    )
    validate_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )
    validate_cmd.add_argument(
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
        available_commands = ["update", "create", "delete", "ls", "drift", "changeset"]
        fzf = Pyfzf()
        for command in available_commands:
            fzf.append_fzf("%s\n" % command)
        selected_command = fzf.execute_fzf(
            empty_allow=True, print_col=1, preview="faws cloudformation {} -h"
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
        raise SystemExit

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
