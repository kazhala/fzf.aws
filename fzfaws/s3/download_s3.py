"""s3 download operation

Contains the main function to handle the download operation from s3
"""
import os
import sys
from s3transfer import S3Transfer
from fzfaws.s3.s3 import S3
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.util import get_confirmation
from fzfaws.s3.helper.sync_s3 import sync_s3
from fzfaws.s3.helper.s3progress import S3Progress
from fzfaws.s3.helper.walk_s3_folder import walk_s3_folder


def download_s3(
    profile=False,
    bucket=None,
    local_path=None,
    recursive=False,
    root=False,
    sync=False,
    exclude=[],
    include=[],
    hidden=False,
    version=False,
):
    """download files/'directory' from s3

    handles sync, download file and download recursive
    from a s3 bucket
    glob pattern are first handled through exclude list and then include list

    Args:
        profile: bool or string, use different profile for operation
        bucket: string, path of the s3 bucket if specified
        local_path: string, local path if specified
        recursive: bool, opeate recursivly
        root: bool, search file from root directory
        sync: bool, use sync operation
        exclude: list, list of pattern to exclude file
        include: list, list of pattern to include file after exclude
        hidden: bool, include hidden directory during search
        version: bool, download specific version of file
    Returns:
        None
    Raises:
        InvalidS3PathPattern: when the specified s3 path is invalid pattern
        NoSelectionMade: when the required fzf selection is not made
        SubprocessError: when the local file search got zero result from fzf(no selection in fzf)
    """

    s3 = S3(profile)
    s3.set_bucket_and_path(bucket)
    if not s3.bucket_name:
        s3.set_s3_bucket()
    if recursive or sync:
        if not s3.path_list[0]:
            s3.set_s3_path()
    else:
        if not s3.path_list[0]:
            s3.set_s3_object(multi_select=True, version=version)

    obj_versions = []  # type: list
    if version:
        obj_versions = s3.get_object_version()

    fzf = Pyfzf()
    if not local_path:
        local_path = str(
            fzf.get_local_file(root, directory=True, hidden=hidden, empty_allow=True)
        )

    if sync:
        sync_s3(
            exclude=exclude,
            include=include,
            from_path="s3://%s/%s" % (s3.bucket_name, s3.path_list[0]),
            to_path=local_path,
        )
    elif recursive:
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
                    "download: s3://%s/%s to %s"
                    % (s3.bucket_name, s3_key, dest_pathname)
                )
                transfer = S3Transfer(s3.client)
                transfer.download_file(
                    s3.bucket_name,
                    s3_key,
                    dest_pathname,
                    callback=S3Progress(s3_key, s3.bucket_name, s3.client),
                )
                # remove the progress bar
                sys.stdout.write("\033[2K\033[1G")

    elif version:
        for obj_version in obj_versions:
            destination_path = os.path.join(
                local_path, obj_version.get("Key").split("/")[-1]
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
                    local_path, obj_version.get("Key").split("/")[-1]
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
                transfer = S3Transfer(s3.client)
                transfer.download_file(
                    s3.bucket_name,
                    obj_version.get("Key"),
                    destination_path,
                    extra_args={"VersionId": obj_version.get("VersionId")},
                    callback=S3Progress(
                        obj_version.get("Key"),
                        s3.bucket_name,
                        s3.client,
                        obj_version.get("VersionId"),
                    ),
                )
                # remove the progress bar
                sys.stdout.write("\033[2K\033[1G")

    else:
        for s3_path in s3.path_list:
            destination_path = os.path.join(local_path, s3_path.split("/")[-1])
            # due the fact without recursive flag s3.path_list[0] is set by s3.set_s3_object
            # the bucket_path is the valid s3 key so we don't need to call s3.get_s3_destination_key
            print(
                "(dryrun) download: s3://%s/%s to %s"
                % (s3.bucket_name, s3_path, destination_path)
            )
        if get_confirmation("Confirm?"):
            for s3_path in s3.path_list:
                destination_path = os.path.join(local_path, s3_path.split("/")[-1])
                print(
                    "download: s3://%s/%s to %s"
                    % (s3.bucket_name, s3_path, destination_path)
                )
                transfer = S3Transfer(s3.client)
                transfer.download_file(
                    s3.bucket_name,
                    s3_path,
                    destination_path,
                    callback=S3Progress(s3_path, s3.bucket_name, s3.client),
                )
                # remove the progress bar
                sys.stdout.write("\033[2K\033[1G")
