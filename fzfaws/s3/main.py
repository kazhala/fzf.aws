"""Contains the main entry point for all s3 operations."""
import argparse
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
        description="perform CRUD operations with aws s3 bucket",
        usage="fzfaws s3 [-h] {upload,download,delete,bucket,presign,object,ls} ...",
    )
    subparsers = parser.add_subparsers(dest="subparser_name")

    upload_cmd = subparsers.add_parser(
        "upload", description="upload a local file/directory to s3 bucket"
    )
    upload_cmd.add_argument(
        "-R",
        "--root",
        action="store_true",
        default=False,
        help="search local file from root directory",
    )
    upload_cmd.add_argument(
        "-b",
        "--bucketpath",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/)"
        + "using this flag and skip s3 bucket/path selection",
    )
    upload_cmd.add_argument(
        "-p",
        "--path",
        nargs="+",
        action="store",
        default=[],
        help="specify the path/paths of a local file to upload"
        + "(e.g. ~/folder/ or ~/folder/filename)",
    )
    upload_cmd.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        default=False,
        help="upload a directory to s3 bucket recursivly",
    )
    upload_cmd.add_argument(
        "-s",
        "--sync",
        action="store_true",
        default=False,
        help="use the aws cli s3 sync operation",
    )
    upload_cmd.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        action="store",
        default=[],
        help="specify a number of bash style globbing pattern to exclude a number of patterns",
    )
    upload_cmd.add_argument(
        "-i",
        "--include",
        nargs="+",
        action="store",
        default=[],
        help="specify a number of bash style globbing pattern to include files after excluding",
    )
    upload_cmd.add_argument(
        "-H",
        "--hidden",
        action="store_true",
        default=False,
        help="when fd is installed, add this flag to include hidden files in the search",
    )
    upload_cmd.add_argument(
        "-E",
        "--extra",
        action="store_true",
        default=False,
        help="configure extra settings for this upload operation (e.g. ACL, storage class, encryption)"
        + "otherwise, default settings of the bucket would be used",
    )
    upload_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )

    download_cmd = subparsers.add_parser(
        "download", description="download a file/directory from s3 to local"
    )
    download_cmd.add_argument(
        "-R",
        "--root",
        action="store_true",
        default=False,
        help="search local directory from root directory",
    )
    download_cmd.add_argument(
        "-b",
        "--bucketpath",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketname/filename or bucketname/path/ or bucketName/)"
        + "using this flag and skip s3 bucket/path selection",
    )
    download_cmd.add_argument(
        "-p",
        "--path",
        nargs=1,
        action="store",
        default=[],
        help="specify the path for the download destination of the s3 object"
        + "(e.g. ~/folder/ or ~/folder/filename)",
    )
    download_cmd.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        default=False,
        help="download a directory from s3 recursivly",
    )
    download_cmd.add_argument(
        "-s",
        "--sync",
        action="store_true",
        default=False,
        help="use the aws cli s3 sync operation",
    )
    download_cmd.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        action="store",
        default=[],
        help="specify a number of bash style globbing pattern to exclude a number of patterns",
    )
    download_cmd.add_argument(
        "-i",
        "--include",
        nargs="+",
        action="store",
        default=[],
        help="specify a number of bash style globbing pattern to include files after excluding",
    )
    download_cmd.add_argument(
        "-H",
        "--hidden",
        action="store_true",
        default=False,
        help="when fd is installed, add this flag to include hidden files in the search",
    )
    download_cmd.add_argument(
        "-v",
        "--version",
        action="store_true",
        default=False,
        help="choose a version of the object and download, Note: does not support recursive flag",
    )
    download_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )

    bucket_cmd = subparsers.add_parser(
        "bucket", description="move file/directory between s3 buckets"
    )
    bucket_cmd.add_argument(
        "-b",
        "--bucketpath",
        nargs=1,
        action="store",
        default=[],
        help="sepcify which bucket contains files to move and skip fzf selection",
    )
    bucket_cmd.add_argument(
        "-t",
        "--to",
        nargs=1,
        action="store",
        default=[],
        help="specify the destination bucket and skip fzf selection",
    )
    bucket_cmd.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        default=False,
        help="move bucket object respectively",
    )
    bucket_cmd.add_argument(
        "-s",
        "--sync",
        action="store_true",
        default=False,
        help="use the aws cli s3 sync operation",
    )
    bucket_cmd.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        action="store",
        default=[],
        help="specify a number of bash style globbing pattern to exclude a number of patterns",
    )
    bucket_cmd.add_argument(
        "-i",
        "--include",
        nargs="+",
        action="store",
        default=[],
        help="specify a number of bash style globbing pattern to include files after excluding",
    )
    bucket_cmd.add_argument(
        "-v",
        "--version",
        action="store_true",
        default=False,
        help="choose a version of the object and transfer, Note: does not support recursive flag",
    )
    bucket_cmd.add_argument(
        "-p",
        "--preserve",
        action="store_true",
        default=False,
        help="preserve all object details when moving object, default False, will use the bucket setting",
    )
    bucket_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )

    delete_cmd = subparsers.add_parser(
        "delete", description="delete file/directory on the s3 bucket"
    )
    delete_cmd.add_argument(
        "-b",
        "--bucketpath",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/)"
        + "using this flag and skip s3 bucket/path selection",
    )
    delete_cmd.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        default=False,
        help="download a directory from s3 recursivly",
    )
    delete_cmd.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        action="store",
        default=[],
        help="specify a number of bash style globbing pattern to exclude a number of patterns",
    )
    delete_cmd.add_argument(
        "-i",
        "--include",
        nargs="+",
        action="store",
        default=[],
        help="specify a number of bash style globbing pattern to include files after excluding",
    )
    delete_cmd.add_argument(
        "-m",
        "--mfa",
        nargs=2,
        action="store",
        default=[],
        help="Two argument needed to be specifies, the authentication device's serial number "
        + "and the value that is displayed on your authentication device. "
        + "Required to permanently delete a versioned object if versioning is configured with MFA delete enabled",
    )
    delete_cmd.add_argument(
        "-v",
        "--version",
        action="store_true",
        default=False,
        help="choose an or multiple object versions to delete, Note: does not support recursive, to delete all versions recursivly, use -V flag",
    )
    delete_cmd.add_argument(
        "-V",
        "--allversion",
        action="store_true",
        default=False,
        help="delete a versioned object completely including all versions and delete markes",
    )
    delete_cmd.add_argument(
        "-d",
        "--deletemark",
        action="store_true",
        default=False,
        help="only display and delete object with delete marker, used for cleanup all deleted unwanted object",
    )
    delete_cmd.add_argument(
        "-c",
        "--clean",
        action="store_true",
        default=False,
        help="delete all versions recursivly except the current one, used for cleanup s3 bucket with all older versions",
    )
    delete_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )

    presign_cmd = subparsers.add_parser(
        "presign",
        description="generate presign url for GET on the selected object based on your current profile permission",
    )
    presign_cmd.add_argument(
        "-b",
        "--bucketpath",
        nargs=1,
        action="store",
        default=[],
        help="spcify a s3 path (buckeName/path), use this flag to skip s3 bucket/path selection",
    )
    presign_cmd.add_argument(
        "-v",
        "--version",
        action="store_true",
        default=False,
        help="generate presign url on a specific version of the object",
    )
    presign_cmd.add_argument(
        "-e",
        "--expires",
        nargs=1,
        action="store",
        default=[3600],
        help="specify a expiration period in seconds, default is 3600 seconds",
    )
    presign_cmd.add_argument(
        "-P",
        "--profile",
        nargs="?",
        action="store",
        default=False,
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )

    object_cmd = subparsers.add_parser(
        "object", description="configure settings and properties of objects in S3"
    )
    object_cmd.add_argument(
        "-b",
        "--bucketpath",
        nargs=1,
        action="store",
        default=[],
        help="specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/)"
        + "using this flag and skip s3 bucket/path selection",
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
        help="update setting/configuration of versions of objects",
    )
    object_cmd.add_argument(
        "-V",
        "--allversion",
        action="store_true",
        default=False,
        help="update setting/configuration for all versions of the selected object",
    )
    object_cmd.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        action="store",
        default=[],
        help="specify a number of bash style globbing pattern to exclude a number of patterns",
    )
    object_cmd.add_argument(
        "-i",
        "--include",
        nargs="+",
        action="store",
        default=[],
        help="specify a number of bash style globbing pattern to include files after excluding",
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
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )

    ls_cmd = subparsers.add_parser(
        "ls", description="display details about selected object"
    )
    ls_cmd.add_argument(
        "--bucketpath",
        nargs=1,
        action="store",
        default=[],
        help="spcify a s3 path (buckeName/path), use this flag to skip s3 bucket/path selection",
    )
    ls_cmd.add_argument(
        "-b",
        "--bucket",
        action="store_true",
        default=False,
        help="display detailed bucket information on the selected bucket",
    )
    ls_cmd.add_argument(
        "-v",
        "--version",
        action="store_true",
        default=False,
        help="display detailed version information on the selected version",
    )
    ls_cmd.add_argument(
        "-d",
        "--deletemark",
        action="store_true",
        default=False,
        help="only list deletemark associated object, and display detailed information on the selected version",
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
        help="use a different profile, set the flag without argument to use fzf and select a profile",
    )
    args = parser.parse_args(raw_args)

    if not raw_args:
        available_commands = ["upload", "download", "bucket", "delete", "object", "ls"]
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
        raise SystemExit

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
