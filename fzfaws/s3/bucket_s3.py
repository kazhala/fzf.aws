"""Contains bucket_s3 function to handle operation between buckets."""
import re
from typing import Dict, List, Optional, Tuple

from botocore.exceptions import ClientError

from fzfaws.s3.helper.get_copy_args import get_copy_args
from fzfaws.s3.helper.s3args import S3Args
from fzfaws.s3.helper.s3progress import S3Progress
from fzfaws.s3.helper.s3transferwrapper import S3TransferWrapper
from fzfaws.s3.helper.sync_s3 import sync_s3
from fzfaws.s3.helper.walk_s3_folder import walk_s3_folder
from fzfaws.s3.s3 import S3
from fzfaws.utils import get_confirmation


def bucket_s3(
    profile: bool = False,
    from_bucket: str = None,
    to_bucket: str = None,
    recursive: bool = False,
    sync: bool = False,
    exclude: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
    version: bool = False,
    preserve: bool = False,
) -> None:
    """Transfer file between buckets.

    Handle transfer file between buckets or even within the same bucket.
    Handle glob pattern through exclude list first than it will process the include to explicit include files.

    :param profile: use a different profile for this operation
    :type profile: str, optional
    :param from_bucket: source bucket
    :type from_bucket: str, optional
    :param to_bucket: destination bucket
    :type to_bucket: str, optional
    :param recursive: recursive copy a folder
    :type recursive: bool, optional
    :param sync: sync s3 buckets
    :type sync: bool, optional
    :param exclude: glob patterns to exclude
    :type exclude: List[str], optional
    :param include: glob patterns to include
    :type include: List[str], optional
    :param version: move object verions
    :type version: bool, optional
    :param perserve: save all object's config instead of using the new bucket's settings
    :type perserve: bool, optional
    """
    if exclude is None:
        exclude = []
    if include is None:
        include = []

    s3 = S3(profile)

    # initialise variables to avoid directly using s3 instance since processing 2 buckets
    target_bucket: str = ""
    target_path: str = ""
    target_path_list: List[str] = []
    dest_bucket: str = ""
    dest_path = ""
    obj_versions: List[Dict[str, str]] = []

    search_folder: bool = True if recursive or sync else False

    if from_bucket:
        target_bucket, target_path, target_path_list = process_path_param(
            from_bucket, s3, search_folder, version=version
        )
    else:
        s3.set_s3_bucket(
            header="set the source bucket which contains the file to transfer"
        )
        target_bucket = s3.bucket_name
        if search_folder:
            s3.set_s3_path()
            target_path = s3.path_list[0]
        else:
            s3.set_s3_object(multi_select=True, version=version)
            target_path_list = s3.path_list[:]
    if version and not search_folder:
        obj_versions = s3.get_object_version()
    # clean up the s3 attributes for next operation
    s3.bucket_name = ""
    s3.path_list[0] = ""

    if to_bucket:
        dest_bucket, dest_path, _ = process_path_param(to_bucket, s3, True)
    else:
        s3.set_s3_bucket(
            header="set the destination bucket where the file should be transfered"
        )
        s3.set_s3_path()
        dest_bucket = s3.bucket_name
        dest_path = s3.path_list[0]

    if sync:
        sync_s3(
            exclude,
            include,
            "s3://%s/%s" % (target_bucket, target_path),
            "s3://%s/%s" % (dest_bucket, dest_path),
        )
    elif recursive:
        recursive_copy(
            s3,
            target_bucket,
            target_path,
            dest_bucket,
            dest_path,
            exclude,
            include,
            preserve,
        )

    elif version:
        copy_version(
            s3,
            dest_bucket,
            dest_path,
            obj_versions,
            target_bucket,
            target_path,
            preserve,
        )

    else:
        # set the s3 instance name and path the destination bucket
        s3.bucket_name = dest_bucket
        s3.path_list[0] = dest_path
        for target_path in target_path_list:
            # process the target key path and get the destination key path
            s3_key = s3.get_s3_destination_key(target_path)
            print(
                "(dryrun) copy: s3://%s/%s to s3://%s/%s"
                % (target_bucket, target_path, dest_bucket, s3_key)
            )
        if get_confirmation("Confirm?"):
            for target_path in target_path_list:
                s3_key = s3.get_s3_destination_key(target_path)
                print(
                    "copy: s3://%s/%s to s3://%s/%s"
                    % (target_bucket, target_path, dest_bucket, s3_key)
                )
                copy_source = {"Bucket": target_bucket, "Key": target_path}
                if not preserve:
                    s3transferwrapper = S3TransferWrapper()
                    s3.client.copy(
                        copy_source,
                        dest_bucket,
                        s3_key,
                        Callback=S3Progress(target_path, target_bucket, s3.client),
                        Config=s3transferwrapper.transfer_config,
                    )
                else:
                    s3.bucket_name = target_bucket
                    copy_and_preserve(
                        s3, target_bucket, target_path, dest_bucket, s3_key
                    )


def copy_version(
    s3: S3,
    dest_bucket: str,
    dest_path: str,
    obj_versions: List[Dict[str, str]],
    target_bucket: str,
    target_path: str,
    preserve: bool,
) -> None:
    """Copy versions of object to other bucket.

    :param s3: S3 instance
    :type s3: S3
    :param dest_bucket: the destination bucket to transfer the object
    :type dest_bucket: str
    :param dest_path: the destination path in the destination bucket
    :type dest_path: str
    :param obj_version: the selected versions through get_object_version()
    :type obj_version: List[Dict[str, str]]
    :param target_bucket: the bucket contains the object to transfer
    :type target_bucket: str
    :param target_path: the object path of the object to be transfered
    :type target_path: str
    :param preserve: preserve previous object details after transfer
    :type preserve: bool
    """
    # set s3 attributes for getting destination key
    s3.bucket_name = dest_bucket
    s3.path_list[0] = dest_path
    for obj_version in obj_versions:
        s3_key = s3.get_s3_destination_key(obj_version.get("Key", ""))
        print(
            "(dryrun) copy: s3://%s/%s to s3://%s/%s with version %s"
            % (
                target_bucket,
                obj_version.get("Key"),
                dest_bucket,
                s3_key,
                obj_version.get("VersionId"),
            )
        )

    if get_confirmation("Confirm?"):
        for obj_version in obj_versions:
            s3_key = s3.get_s3_destination_key(obj_version.get("Key", ""))
            print(
                "copy: s3://%s/%s to s3://%s/%s with version %s"
                % (
                    target_bucket,
                    obj_version.get("Key"),
                    dest_bucket,
                    s3_key,
                    obj_version.get("VersionId"),
                )
            )
            copy_source = {
                "Bucket": target_bucket,
                "Key": obj_version.get("Key"),
                "VersionId": obj_version.get("VersionId"),
            }
            if not preserve:
                s3transferwrapper = S3TransferWrapper()
                s3.client.copy(
                    copy_source,
                    dest_bucket,
                    s3_key,
                    Callback=S3Progress(
                        obj_version.get("Key", ""),
                        target_bucket,
                        s3.client,
                        version_id=obj_version.get("VersionId"),
                    ),
                    Config=s3transferwrapper.transfer_config,
                )
            else:
                s3.bucket_name = target_bucket
                copy_and_preserve(
                    s3,
                    target_bucket,
                    obj_version.get("Key", ""),
                    dest_bucket,
                    s3_key,
                    version=obj_version.get("VersionId"),
                )


def recursive_copy(
    s3: S3,
    target_bucket: str,
    target_path: str,
    dest_bucket: str,
    dest_path: str,
    exclude: List[str],
    include: List[str],
    preserve: bool,
) -> None:
    """Recursive copy object to other bucket.

    :param s3: S3 instance
    :type s3: S3
    :param target_bucket: source bucket
    :type target_bucket: str
    :param target_path: source folder path
    :type target_path: str
    :param dest_bucket: destination bucket
    :type dest_bucket: str
    :param dest_path: dest folder path
    :type dest_path: str
    :param exclude: glob pattern to exclude
    :type exclude: List[str]
    :param include: glob pattern to include
    :type include: List[str]
    :param preserve: preserve previous object config
    :type preserve: bool
    """
    file_list = walk_s3_folder(
        s3.client,
        target_bucket,
        target_path,
        target_path,
        [],
        exclude,
        include,
        "bucket",
        dest_path,
        dest_bucket,
    )

    if get_confirmation("Confirm?"):
        for s3_key, dest_pathname in file_list:
            print(
                "copy: s3://%s/%s to s3://%s/%s"
                % (target_bucket, s3_key, dest_bucket, dest_pathname)
            )
            copy_source = {"Bucket": target_bucket, "Key": s3_key}
            if not preserve:
                s3transferwrapper = S3TransferWrapper()
                s3.client.copy(
                    copy_source,
                    dest_bucket,
                    dest_pathname,
                    Callback=S3Progress(s3_key, target_bucket, s3.client),
                    Config=s3transferwrapper.transfer_config,
                )
            else:
                s3.bucket_name = target_bucket
                copy_and_preserve(s3, target_bucket, s3_key, dest_bucket, dest_pathname)


def copy_and_preserve(
    s3: S3,
    target_bucket: str,
    target_path: str,
    dest_bucket: str,
    dest_path: str,
    version: str = None,
) -> None:
    """Copy object to other buckets and preserve previous details.

    :param s3: S3 instance, make sure contains bucket name
    :type s3: S3
    :param target_bucket: source bucket for upload
    :type target_bucket: str
    :param dest_bucket: destination bucket
    :type dest_bucket: str
    :param dest_path: destination key name
    :type dest_path: str
    :param version: versionID of the object
    :type version: str
    :raises ClientError: clienterror will raise when coping KMS encrypted file, handled internally
    """
    copy_source: Dict[str, str] = {"Bucket": target_bucket, "Key": target_path}
    if version:
        copy_source["VersionId"] = version
    s3_args = S3Args(s3)
    copy_object_args = get_copy_args(
        s3, target_path, s3_args, extra_args=True, version=version
    )

    # limit to one retry
    attempt_count: int = 0
    while attempt_count < 2:
        try:
            attempt_count += 1
            s3transferwrapper = S3TransferWrapper()
            s3.client.copy(
                copy_source,
                dest_bucket,
                dest_path,
                Callback=S3Progress(target_path, s3.bucket_name, s3.client),
                ExtraArgs=copy_object_args,
                Config=s3transferwrapper.transfer_config,
            )
            break
        except ClientError as e:
            error_pattern = r"^.*\((.*)\).*$"
            error_name = re.match(error_pattern, str(e)).group(1)
            if error_name == "AccessDenied":
                print(80 * "-")
                print(e)
                print(
                    "You may have ACL policies that enable public access but "
                    "the destination bucket is blocking all public access, "
                    + "you need to either uncheck 'block all public access' or update your object ACL settings "
                    + "or try again without the -p flag or continue without preserving the ACL"
                )
                if not get_confirmation("Continue without preserving ACL?"):
                    raise
                copy_object_args.pop("GrantFullControl", None)
                copy_object_args.pop("GrantRead", None)
                copy_object_args.pop("GrantReadACP", None)
                copy_object_args.pop("GrantWriteACP", None)
            # # handle when kms encrypt object move to a bucket in different region
            elif error_name == "KMS.NotFoundException":
                copy_object_args["ServerSideEncryption"] = "AES256"
                copy_object_args.pop("SSEKMSKeyId", None)
            else:
                raise


def process_path_param(
    bucket: str, s3: S3, search_folder: bool, version: bool = False
) -> Tuple[str, str, List[str]]:
    """Process bucket parameter and return bucket name and path.

    :param bucket: raw bucket parameter from the command line
    :type bucket: str
    :param search_folder: recursive operation
    :type search_folder: bool
    :param version: include version object
    :type version: bool, optional
    :return: user selected bucket informaiton
    :rtype: Tuple[str, str, List[str]]

    Example return value:
        (kazhala-lol, hello/, [])
    """
    s3.set_bucket_and_path(bucket)
    if not s3.path_list[0]:
        if search_folder:
            s3.set_s3_path()
        else:
            s3.set_s3_object(multi_select=True, version=version)
    return (s3.bucket_name, s3.path_list[0], s3.path_list[:])
