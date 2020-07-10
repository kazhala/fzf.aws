"""Contains function to upload file to s3."""
import os
from typing import Dict, List, Optional, Union

from fzfaws.s3 import S3
from fzfaws.s3.helper.exclude_file import exclude_file
from fzfaws.s3.helper.s3args import S3Args
from fzfaws.s3.helper.s3progress import S3Progress
from fzfaws.s3.helper.s3transferwrapper import S3TransferWrapper
from fzfaws.s3.helper.sync_s3 import sync_s3
from fzfaws.utils import Pyfzf, get_confirmation


def upload_s3(
    profile: bool = False,
    bucket: str = None,
    local_paths: Optional[Union[str, list]] = None,
    recursive: bool = False,
    hidden: bool = False,
    search_root: bool = False,
    sync: bool = False,
    exclude: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
    extra_config: bool = False,
) -> None:
    """Upload local files/directories to s3.

    Upload through boto3 s3 client.
    Glob pattern exclude list are handled first then handle the include list.

    :param profile: profile to use for this operation
    :type profile: bool, optional
    :param bucket: specify bucket to upload
    :type bucket: str, optional
    :param local_paths: local file paths to upload
    :type local_paths: list, optional
    :param recursive: upload directory
    :type recursive: bool, optional
    :param hidden: include hidden files during search
    :type hidden: bool, optional
    :param search_root: search from root
    :type search_root: bool, optional
    :param sync: use aws cli s3 sync
    :type sync: bool, optional
    :param exclude: glob patterns to exclude
    :type exclude: List[str], optional
    :param include: glob patterns to include
    :type include: List[str], optional
    :param extra_config: configure extra settings during upload
    :type extra_config: bool, optional
    """
    if not local_paths:
        local_paths = []
    if not exclude:
        exclude = []
    if not include:
        include = []

    s3 = S3(profile)
    s3.set_bucket_and_path(bucket)
    if not s3.bucket_name:
        s3.set_s3_bucket()
    if not s3.path_list[0]:
        s3.set_s3_path()

    if not local_paths:
        fzf = Pyfzf()
        recursive = True if recursive or sync else False
        # don't allow multi_select for recursive operation
        multi_select = True if not recursive else False
        local_paths = fzf.get_local_file(
            search_from_root=search_root,
            directory=recursive,
            hidden=hidden,
            empty_allow=recursive,
            multi_select=multi_select,
        )

    # get the first item from the array since recursive operation doesn't support multi_select
    # local_path is used for sync and recursive operation
    # local_paths is used for single file operation
    if isinstance(local_paths, list):
        local_path = str(local_paths[0])
    else:
        local_path = str(local_paths)

    # construct extra argument
    extra_args = S3Args(s3)
    if extra_config:
        extra_args.set_extra_args(upload=True)

    if sync:
        sync_s3(
            exclude=exclude,
            include=include,
            from_path=local_path,
            to_path="s3://%s/%s" % (s3.bucket_name, s3.path_list[0]),
        )

    elif recursive:
        recursive_upload(s3, local_path, exclude, include, extra_args)

    else:
        for filepath in local_paths:
            # get the formated s3 destination
            destination_key = s3.get_s3_destination_key(filepath)
            print(
                "(dryrun) upload: %s to s3://%s/%s"
                % (filepath, s3.bucket_name, destination_key)
            )

        if get_confirmation("Confirm?"):
            for filepath in local_paths:
                destination_key = s3.get_s3_destination_key(filepath)
                print(
                    "upload: %s to s3://%s/%s"
                    % (filepath, s3.bucket_name, destination_key)
                )
                transfer = S3TransferWrapper(s3.client)
                transfer.s3transfer.upload_file(
                    filepath,
                    s3.bucket_name,
                    destination_key,
                    callback=S3Progress(filepath),
                    extra_args=extra_args.extra_args,
                )


def recursive_upload(
    s3: S3, local_path: str, exclude: List[str], include: List[str], extra_args: S3Args
) -> None:
    """Recursive upload local directory to s3.

    Perform a os.walk to upload everyfile under a directory.

    :param s3: S3 instance
    :type s3: S3
    :param local_path: local directory
    :type local_path: str
    :param exclude: glob pattern to exclude
    :type exclude: List[str]
    :param include: glob pattern to include
    :type include: List[str]
    :param extra_args: S3Args instance to set extra argument
    :type extra_args: S3Args
    """
    upload_list: List[Dict[str, str]] = []
    for root, _, files in os.walk(local_path):
        for filename in files:
            full_path = os.path.join(root, filename)
            relative_path = os.path.relpath(full_path, local_path)

            if not exclude_file(exclude, include, relative_path):
                destination_key = s3.get_s3_destination_key(
                    relative_path, recursive=True
                )
                print(
                    "(dryrun) upload: %s to s3://%s/%s"
                    % (relative_path, s3.bucket_name, destination_key)
                )
                upload_list.append(
                    {
                        "local_path": full_path,
                        "bucket": s3.bucket_name,
                        "key": destination_key,
                        "relative": relative_path,
                    }
                )

    if get_confirmation("Confirm?"):
        for item in upload_list:
            print(
                "upload: %s to s3://%s/%s"
                % (item["relative"], item["bucket"], item["key"])
            )
            transfer = S3TransferWrapper(s3.client)
            transfer.s3transfer.upload_file(
                item["local_path"],
                item["bucket"],
                item["key"],
                callback=S3Progress(item["local_path"]),
                extra_args=extra_args.extra_args,
            )
