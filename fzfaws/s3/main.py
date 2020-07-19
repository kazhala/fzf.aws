"""Contains the main entry point for all s3 operations."""
import argparse
import sys
from typing import Any, List

from fzfaws.s3.bucket_s3 import bucket_s3
from fzfaws.s3.delete_s3 import delete_s3
from fzfaws.s3.download_s3 import download_s3
from fzfaws.s3.ls_s3 import ls_s3
from fzfaws.s3.object_s3 import object_s3
from fzfaws.s3.presign_s3 import presign_s3
from fzfaws.s3.upload_s3 import upload_s3
from fzfaws.utils.pyfzf import Pyfzf


def s3(raw_args: List[Any]) -> None:
    """Parse arguments and direct traffic to handler, internal use only.

    The raw_args are the processed args through cli.py main function.
    It also already contains the user default args so no need to process
    default args anymore.

    :param raw_args: list of args to be parsed
    :type raw_args: list
    """
    parser = argparse.ArgumentParser(
        description="Perform operations and interact with aws S3 bucket.",
        prog="fzfaws s3",
    )
    subparsers = parser.add_subparsers(dest="subparser_name")

    upload_cmd = subparsers.add_parser(
        "upload", description="Upload local files/directories to s3 bucket."
    )
    upload_cmd.add_argument(
        "-R",
        "--root",
        action="store_true",
        default=False,
        help="search local files/directories from root",
    )
    upload_cmd.add_argument(
        "-b",
        "--bucketpath",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/) and skip s3 bucket/path selection",
    )
    upload_cmd.add_argument(
        "-p",
        "--path",
        nargs="+",
        action="store",
        default=[],
        help="specify paths for local files/directories to upload (e.g. ~/folder/ or ~/folder/filename)",
    )
    upload_cmd.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        default=False,
        help="upload directories to s3 bucket recursivly",
    )
    upload_cmd.add_argument(
        "-s",
        "--sync",
        action="store_true",
        default=False,
        help="use the aws-cli s3 sync operation",
    )
    upload_cmd.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        action="store",
        default=[],
        help="specify bash style globbing patterns to exclude during the operation",
    )
    upload_cmd.add_argument(
        "-i",
        "--include",
        nargs="+",
        action="store",
        default=[],
        help="specify bash style globbing patterns to include during the operation",
    )
    upload_cmd.add_argument(
        "-H",
        "--hidden",
        action="store_true",
        default=False,
        help="include hidden files during file search, useful when fd is installed",
    )
    upload_cmd.add_argument(
        "-E",
        "--extra",
        action="store_true",
        default=False,
        help="configure extra settings for the upload operation (e.g. ACL, StorageClass, Encryption)",
    )
    upload_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a profile for the operation",
    )

    download_cmd = subparsers.add_parser(
        "download", description="Download files/directories from s3."
    )
    download_cmd.add_argument(
        "-R",
        "--root",
        action="store_true",
        default=False,
        help="search local directories from root",
    )
    download_cmd.add_argument(
        "-b",
        "--bucketpath",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/) and skip s3 bucket/path selection",
    )
    download_cmd.add_argument(
        "-p",
        "--path",
        nargs=1,
        action="store",
        default=[],
        help="specify path for the download destination of the s3 object (e.g. ~/folder/ or ~/folder/filename)",
    )
    download_cmd.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        default=False,
        help="download directory from s3 recursivly",
    )
    download_cmd.add_argument(
        "-s",
        "--sync",
        action="store_true",
        default=False,
        help="use the aws-cli s3 sync operation",
    )
    download_cmd.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        action="store",
        default=[],
        help="specify bash style globbing patterns to exclude during the operation",
    )
    download_cmd.add_argument(
        "-i",
        "--include",
        nargs="+",
        action="store",
        default=[],
        help="specify bash style globbing patterns to include during the operation",
    )
    download_cmd.add_argument(
        "-H",
        "--hidden",
        action="store_true",
        default=False,
        help="include hidden directories during directory search, useful when fd is installed",
    )
    download_cmd.add_argument(
        "-v",
        "--version",
        action="store_true",
        default=False,
        help="choose versions of the object to download, does not support recursive flag",
    )
    download_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a profile for the operation",
    )

    bucket_cmd = subparsers.add_parser(
        "bucket", description="Move files/directories between s3 buckets."
    )
    bucket_cmd.add_argument(
        "-b",
        "--bucketpath",
        nargs=1,
        action="store",
        default=[],
        help="specify the source bucket and skip bucket/path selection",
    )
    bucket_cmd.add_argument(
        "-t",
        "--to",
        nargs=1,
        action="store",
        default=[],
        help="specify the destination bucket and skip bucket/path selection",
    )
    bucket_cmd.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        default=False,
        help="move bucket directories recursively",
    )
    bucket_cmd.add_argument(
        "-s",
        "--sync",
        action="store_true",
        default=False,
        help="use the aws-cli s3 sync operation",
    )
    bucket_cmd.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        action="store",
        default=[],
        help="specify bash style globbing patterns to exclude during the operation",
    )
    bucket_cmd.add_argument(
        "-i",
        "--include",
        nargs="+",
        action="store",
        default=[],
        help="specify bash style globbing patterns to include during the operation",
    )
    bucket_cmd.add_argument(
        "-v",
        "--version",
        action="store_true",
        default=False,
        help="choose versions of the object and transfer, does not support recursive flag",
    )
    bucket_cmd.add_argument(
        "-p",
        "--preserve",
        action="store_true",
        default=False,
        help="preserve object details when moving object (e.g. StorageClass, ACL, Encryption)",
    )
    bucket_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a profile for the operation",
    )

    delete_cmd = subparsers.add_parser(
        "delete", description="Delete files/directories on s3."
    )
    delete_cmd.add_argument(
        "-b",
        "--bucketpath",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/) and skip s3 bucket/path selection",
    )
    delete_cmd.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        default=False,
        help="delete directories from s3 recursivly",
    )
    delete_cmd.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        action="store",
        default=[],
        help="specify bash style globbing patterns to exclude during the operation",
    )
    delete_cmd.add_argument(
        "-i",
        "--include",
        nargs="+",
        action="store",
        default=[],
        help="specify bash style globbing patterns to include during the operation",
    )
    delete_cmd.add_argument(
        "-m",
        "--mfa",
        nargs=2,
        action="store",
        default=[],
        help="perform MFA deletion, require two arguments: the authentication device serial number "
        + "and the value that is displayed on the authentication device, does not support multiple operations",
    )
    delete_cmd.add_argument(
        "-v",
        "--version",
        action="store_true",
        default=False,
        help="choose object versions to delete, does not support recursive, to delete all versions recursivly, use -V flag",
    )
    delete_cmd.add_argument(
        "-V",
        "--allversion",
        action="store_true",
        default=False,
        help="delete versioned objects completely including all versions and delete markers",
    )
    delete_cmd.add_argument(
        "-d",
        "--deletemark",
        action="store_true",
        default=False,
        help="only display and delete object with delete marker, useful for cleaning up all objects with delete marker",
    )
    delete_cmd.add_argument(
        "-c",
        "--clean",
        action="store_true",
        default=False,
        help="delete all versions recursivly except the current version, useful for cleaning up versioned s3 bucket",
    )
    delete_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a profile for the operation",
    )

    presign_cmd = subparsers.add_parser(
        "presign",
        description="Generate presign url for GET operation on the selected object based on the current profile permission.",
    )
    presign_cmd.add_argument(
        "-b",
        "--bucketpath",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketName/filename) and skip s3 bucket/path selection",
    )
    presign_cmd.add_argument(
        "-v",
        "--version",
        action="store_true",
        default=False,
        help="generate presign url on specific object versions",
    )
    presign_cmd.add_argument(
        "-e",
        "--expires",
        nargs=1,
        action="store",
        default=[3600],
        help="specify an expiration period in seconds, default is 3600 seconds",
    )
    presign_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a profile for the operation",
    )

    object_cmd = subparsers.add_parser(
        "object", description="Configure settings and properties of s3 objects."
    )
    object_cmd.add_argument(
        "-b",
        "--bucketpath",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/) and skip s3 bucket/path selection",
    )
    object_cmd.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        default=False,
        help="update setting/configuration of a 'folder' recursivly on s3",
    )
    object_cmd.add_argument(
        "-v",
        "--version",
        action="store_true",
        default=False,
        help="update setting/configuration of objects versions",
    )
    object_cmd.add_argument(
        "-V",
        "--allversion",
        action="store_true",
        default=False,
        help="update setting/configuration for all versions of the selected objects",
    )
    object_cmd.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        action="store",
        default=[],
        help="specify bash style globbing pattern to exclude during the operation",
    )
    object_cmd.add_argument(
        "-i",
        "--include",
        nargs="+",
        action="store",
        default=[],
        help="specify bash style globbing pattern to include during the operation",
    )
    object_cmd.add_argument(
        "-n",
        "--name",
        action="store_true",
        default=False,
        help="update the name of the selected object",
    )
    object_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a profile for the operation",
    )

    ls_cmd = subparsers.add_parser(
        "ls", description="Display details about selected objects/bucket."
    )
    ls_cmd.add_argument(
        "--bucketpath",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/) and skip s3 bucket/path selection",
    )
    ls_cmd.add_argument(
        "-b",
        "--bucket",
        action="store_true",
        default=False,
        help="display detailed bucket information",
    )
    ls_cmd.add_argument(
        "-v",
        "--version",
        action="store_true",
        default=False,
        help="display detailed object version information",
    )
    ls_cmd.add_argument(
        "-d",
        "--deletemark",
        action="store_true",
        default=False,
        help="only list object associated with delete marker, and display detailed information on the selected version",
    )
    ls_cmd.add_argument(
        "--url",
        action="store_true",
        default=False,
        help="display the s3 url for the selected object/bucket",
    )
    ls_cmd.add_argument(
        "--uri",
        action="store_true",
        default=False,
        help="display the s3 uri for the selected object/bucket",
    )
    ls_cmd.add_argument(
        "--name",
        action="store_true",
        default=False,
        help="display the selected s3 bucket/object name",
    )
    ls_cmd.add_argument(
        "--arn",
        action="store_true",
        default=False,
        help="display the selected object/bucket arn",
    )
    ls_cmd.add_argument(
        "--versionid",
        action="store_true",
        default=False,
        help="display the selected object version's versionid",
    )
    ls_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="choose/specify a profile for the operation",
    )
    args = parser.parse_args(raw_args)

    if not raw_args:
        available_commands = [
            "upload",
            "download",
            "bucket",
            "delete",
            "object",
            "ls",
            "presign",
        ]
        fzf = Pyfzf()
        for command in available_commands:
            fzf.append_fzf(command)
            fzf.append_fzf("\n")
        selected_command = fzf.execute_fzf(
            empty_allow=True, print_col=1, preview="fzfaws s3 {} -h"
        )
        if selected_command == "upload":
            upload_cmd.print_help()
        elif selected_command == "download":
            download_cmd.print_help()
        elif selected_command == "bucket":
            bucket_cmd.print_help()
        elif selected_command == "delete":
            delete_cmd.print_help()
        elif selected_command == "object":
            object_cmd.print_help()
        elif selected_command == "ls":
            ls_cmd.print_help()
        elif selected_command == "presign":
            presign_cmd.print_help()
        sys.exit(0)

    if args.profile == None:
        # when user set --profile flag but without argument
        args.profile = True
    if hasattr(args, "bucketpath") and args.subparser_name != "bucket":
        args.bucketpath = args.bucketpath[0] if args.bucketpath else None

    if args.subparser_name == "upload":
        upload_s3(
            args.profile,
            args.bucketpath,
            args.path,
            args.recursive,
            args.hidden,
            args.root,
            args.sync,
            args.exclude,
            args.include,
            args.extra,
        )
    elif args.subparser_name == "download":
        local_path = args.path[0] if args.path else None
        download_s3(
            args.profile,
            args.bucketpath,
            local_path,
            args.recursive,
            args.root,
            args.sync,
            args.exclude,
            args.include,
            args.hidden,
            args.version,
        )
    elif args.subparser_name == "bucket":
        from_bucket = args.bucketpath[0] if args.bucketpath else None
        to_bucket = args.to[0] if args.to else None
        bucket_s3(
            args.profile,
            from_bucket,
            to_bucket,
            args.recursive,
            args.sync,
            args.exclude,
            args.include,
            args.version,
            args.preserve,
        )
    elif args.subparser_name == "delete":
        mfa = " ".join(args.mfa)
        delete_s3(
            args.profile,
            args.bucketpath,
            args.recursive,
            args.exclude,
            args.include,
            mfa,
            args.version,
            args.allversion,
            args.deletemark,
            args.clean,
        )
    elif args.subparser_name == "presign":
        presign_s3(args.profile, args.bucketpath, args.version, int(args.expires[0]))
    elif args.subparser_name == "object":
        object_s3(
            args.profile,
            args.bucketpath,
            args.recursive,
            args.version,
            args.allversion,
            args.exclude,
            args.include,
            args.name,
        )
    elif args.subparser_name == "ls":
        ls_s3(
            args.profile,
            args.bucket,
            args.version,
            args.deletemark,
            args.url,
            args.uri,
            args.name,
            args.arn,
            args.versionid,
            args.bucketpath,
        )
