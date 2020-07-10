"""Contains function to download file from s3."""
import os
from typing import Dict, List, Optional, Union

from fzfaws.s3.helper.s3progress import S3Progress
from fzfaws.s3.helper.s3transferwrapper import S3TransferWrapper
from fzfaws.s3.helper.sync_s3 import sync_s3
from fzfaws.s3.helper.walk_s3_folder import walk_s3_folder
from fzfaws.s3.s3 import S3
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.util import get_confirmation


def download_s3(
    profile: Union[str, bool] = False,
    bucket: str = None,
    local_path: str = None,
    recursive: bool = False,
    search_from_root: bool = False,
    sync: bool = False,
    exclude: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
    hidden: bool = False,
    version: bool = False,
) -> None:
    """Download files/'directory' from s3.

    Handles sync, download file and download recursive from a s3 bucket.
    Glob pattern are first handled through exclude list and then include list.

    :param profile: profile to use for this operation
    :type profile: bool, optional
    :param bucket: specify bucket to download
    :type bucket: str, optional
    :param local_paths: local file path for download
    :type local_paths: str, optional
    :param recursive: download s3 directory
    :type recursive: bool, optional
    :param search_root: search from root
    :type search_root: bool, optional
    :param sync: use aws cli s3 sync
    :type sync: bool, optional
    :param exclude: glob patterns to exclude
    :type exclude: List[str], optional
    :param include: glob patterns to include
    :type include: List[str], optional
    :param hidden: include hidden files during search
    :type hidden: bool, optional
    :param version: download version object
    :type version: bool, optional
    """
    if not exclude:
        exclude = []
    if not include:
        include = []

    s3 = S3(profile)
    s3.set_bucket_and_path(bucket)
    if not s3.bucket_name:
        s3.set_s3_bucket()
    if recursive or sync:
        if not s3.path_list[0]:
            s3.set_s3_path(download=True)
    else:
        if not s3.path_list[0]:
            s3.set_s3_object(multi_select=True, version=version)

    obj_versions: List[Dict[str, str]] = []
    if version:
        obj_versions = s3.get_object_version()

    if not local_path:
        fzf = Pyfzf()
        local_path = str(
            fzf.get_local_file(
                search_from_root, directory=True, hidden=hidden, empty_allow=True
            )
        )

    if sync:
        sync_s3(
            exclude=exclude,
            include=include,
            from_path="s3://%s/%s" % (s3.bucket_name, s3.path_list[0]),
            to_path=local_path,
        )
    elif recursive:
        download_recusive(s3, exclude, include, local_path)

    elif version:
        download_version(s3, obj_versions, local_path)

    else:
        for s3_path in s3.path_list:
            destination_path = os.path.join(local_path, os.path.basename(s3_path))
            # due the fact without recursive flag s3.path_list[0] is set by s3.set_s3_object
            # the bucket_path is the valid s3 key so we don't need to call s3.get_s3_destination_key
            print(
                "(dryrun) download: s3://%s/%s to %s"
                % (s3.bucket_name, s3_path, destination_path)
            )
        if get_confirmation("Confirm?"):
            for s3_path in s3.path_list:
                destination_path = os.path.join(local_path, os.path.basename(s3_path))
                print(
                    "download: s3://%s/%s to %s"
                    % (s3.bucket_name, s3_path, destination_path)
                )
                transfer = S3TransferWrapper(s3.client)
                transfer.s3transfer.download_file(
                    s3.bucket_name,
                    s3_path,
                    destination_path,
                    callback=S3Progress(s3_path, s3.bucket_name, s3.client),
                )


def download_recusive(
    s3: S3, exclude: List[str], include: List[str], local_path: str
) -> None:
    """Download s3 recursive.

    :param s3: S3 instance
    :type s3: S3
    :param exclude: glob pattern to exclude
    :type exclude: List[str]
    :param include: glob pattern to include
    :type include: List[str]
    :param local_path: local directory to download
    :type local_path: str
    """
    download_list = walk_s3_folder(
        s3.client,
        s3.bucket_name,
        s3.path_list[0],
        s3.path_list[0],
        [],
        exclude,
        include,
        "download",
        local_path,
    )

    if get_confirmation("Confirm?"):
        for s3_key, dest_pathname in download_list:
            if not os.path.exists(os.path.dirname(dest_pathname)):
                os.makedirs(os.path.dirname(dest_pathname))
            print(
                "download: s3://%s/%s to %s" % (s3.bucket_name, s3_key, dest_pathname)
            )
            transfer = S3TransferWrapper(s3.client)
            transfer.s3transfer.download_file(
                s3.bucket_name,
                s3_key,
                dest_pathname,
                callback=S3Progress(s3_key, s3.bucket_name, s3.client),
            )


def download_version(
    s3: S3, obj_versions: List[Dict[str, str]], local_path: str
) -> None:
    """Download versions of a object.

    :param s3: instance of S3
    :type s3: S3
    :param obj_versions: list of object and their versions to download
    :type obj_versions: List[Dict[str, str]]
    :param local_path: local directory to download
    :type local_path: str
    """
    for obj_version in obj_versions:
        destination_path = os.path.join(
            local_path, os.path.basename(obj_version.get("Key", ""))
        )
        print(
            "(dryrun) download: s3://%s/%s to %s with version %s"
            % (
                s3.bucket_name,
                obj_version.get("Key"),
                destination_path,
                obj_version.get("VersionId"),
            )
        )

    if get_confirmation("Confirm"):
        for obj_version in obj_versions:
            destination_path = os.path.join(
                local_path, os.path.basename(obj_version.get("Key", ""))
            )
            print(
                "download: s3://%s/%s to %s with version %s"
                % (
                    s3.bucket_name,
                    obj_version.get("Key"),
                    destination_path,
                    obj_version.get("VersionId"),
                )
            )
            transfer = S3TransferWrapper(s3.client)
            transfer.s3transfer.download_file(
                s3.bucket_name,
                obj_version.get("Key"),
                destination_path,
                extra_args={"VersionId": obj_version.get("VersionId")},
                callback=S3Progress(
                    obj_version.get("Key", ""),
                    s3.bucket_name,
                    s3.client,
                    obj_version.get("VersionId"),
                ),
            )
