"""Contains function for handling delete operation on s3."""
from typing import Dict, List, Optional, Union

import boto3

from fzfaws.s3.helper.exclude_file import exclude_file
from fzfaws.s3.helper.walk_s3_folder import walk_s3_folder
from fzfaws.s3.s3 import S3
from fzfaws.utils.util import get_confirmation


def delete_s3(
    profile: Union[str, bool] = False,
    bucket: str = None,
    recursive: bool = False,
    exclude: Optional[List[str]] = [],
    include: Optional[List[str]] = [],
    mfa: str = "",
    version: bool = False,
    allversion: bool = False,
    deletemark: bool = False,
    clean: bool = False,
) -> None:
    """Delete file/directory on the selected s3 bucket.

    :param profile: use a different profile for this operation
    :type profile: Union[str, bool], optional
    :param bucket: specify a bucket to operate
    :type bucket: str, optional
    :param recursive: recursive delete
    :type recursive: bool, optional
    :param exclude: glob pattern to exclude
    :type exclude: List[str], optional
    :param include: glob pattern to include
    :type include: List[str], optional
    :param mfa: specify mfa information to operate MFA delete
    :type mfa: str, optional
    :param version: delete selected version
    :type version: bool, optional
    :param allversion: skip selection of version, delete all versions
    :type allversion: bool, optional
    :param deletemark: only display files with delete mark
    :type deletemark: bool, optional
    :param clean: recusive delete all olderversions but leave the current version
    :type clean: bool, optional
    """
    if exclude is None:
        exclude = []
    if include is None:
        include = []

    s3 = S3(profile)

    if deletemark:
        version = True
    if allversion:
        version = True
    if clean:
        version = True
        allversion = True
        recursive = True
    if mfa:
        # mfa operation can only operate on one object
        # because each time, it will require a new mfa code
        recursive = False
        allversion = False
        clean = False

    s3.set_bucket_and_path(bucket)
    if not s3.bucket_name:
        s3.set_s3_bucket()
    if recursive:
        if not s3.path_list[0]:
            s3.set_s3_path()
    else:
        if not s3.path_list[0]:
            s3.set_s3_object(
                version=version,
                multi_select=True if not mfa else False,
                deletemark=deletemark,
            )

    if recursive:
        delete_object_recursive(s3, exclude, include, deletemark, clean, allversion)

    elif version:
        delete_object_version(s3, allversion, mfa)

    else:
        # due the fact without recursive flag s3.bucket_path is set by s3.set_s3_object
        # the bucket_path is the valid s3 key so we don't need to call s3.get_s3_destination_key
        for s3_path in s3.path_list:
            print("(dryrun) delete: s3://%s/%s" % (s3.bucket_name, s3_path))
        if get_confirmation("Confirm?"):
            for s3_path in s3.path_list:
                print("delete: s3://%s/%s" % (s3.bucket_name, s3_path))
                s3.client.delete_object(
                    Bucket=s3.bucket_name, Key=s3_path,
                )


def delete_object_version(s3: S3, allversion: bool = False, mfa: str = "") -> None:
    """Delete versions of a object.

    :param s3: S3 instance
    :type s3: S3
    :param allversion: skip verison selection and select all verions
    :type allversion: bool, optional
    :param mfa: mfa serial number and code seperate by space to use mfa privilage
    :type mfa: str, optional
    """
    obj_versions = s3.get_object_version(
        delete=True, select_all=allversion, multi_select=True if not mfa else False
    )

    for obj_version in obj_versions:
        print(
            "(dryrun) delete: s3://%s/%s with version %s"
            % (s3.bucket_name, obj_version.get("Key"), obj_version.get("VersionId"))
        )
    if get_confirmation("Confirm?"):
        for obj_version in obj_versions:
            print(
                "delete: s3://%s/%s with version %s"
                % (
                    s3.bucket_name,
                    obj_version.get("Key"),
                    obj_version.get("VersionId"),
                )
            )
            s3.client.delete_object(
                Bucket=s3.bucket_name,
                Key=obj_version.get("Key"),
                MFA=mfa,
                VersionId=obj_version.get("VersionId"),
            )


def delete_object_recursive(
    s3: S3,
    exclude: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
    deletemark: bool = False,
    clean: bool = False,
    allversion: bool = False,
) -> None:
    """Recursive delete object and their versions if specified.

    :param s3: S3 instance
    :type s3: S3
    :param exclude: glob pattern to exclude
    :type exclude: List[str], optional
    :param include: glob pattern to include
    :type include: List[str], optional
    :param deletemark: only delete deletemarkers
    :type deletemark: bool, optional
    :param clean: delete all versions except the current version
    :type clean: bool, optional
    :param allversion: delete allversions, use to nuke the entire bucket or folder
    :type allversion: bool, optional
    """
    if allversion:
        # use a different method other than the walk s3 folder
        # since walk_s3_folder doesn't provide access to deleted version object
        # delete_all_versions method will list all files including deleted versions or even delete marker
        file_list = find_all_version_files(
            s3.client,
            s3.bucket_name,
            s3.path_list[0],
            [],
            exclude,
            include,
            deletemark,
        )
        obj_versions: List[Dict[str, str]] = []

        # loop through all files and get their versions
        for file in file_list:
            obj_versions.extend(
                s3.get_object_version(
                    key=file, delete=True, select_all=True, non_current=clean
                )
            )
            print(
                "(dryrun) delete: s3://%s/%s %s"
                % (
                    s3.bucket_name,
                    file,
                    "with all versions" if not clean else "all non-current versions",
                )
            )

        if get_confirmation(
            "Delete %s?"
            % ("all of their versions" if not clean else "all non-current versions")
        ):
            for obj_version in obj_versions:
                print(
                    "delete: s3://%s/%s with version %s"
                    % (
                        s3.bucket_name,
                        obj_version.get("Key"),
                        obj_version.get("VersionId"),
                    )
                )
                s3.client.delete_object(
                    Bucket=s3.bucket_name,
                    Key=obj_version.get("Key"),
                    VersionId=obj_version.get("VersionId"),
                )

    else:
        file_list = walk_s3_folder(
            s3.client,
            s3.bucket_name,
            s3.path_list[0],
            s3.path_list[0],
            [],
            exclude,
            include,
            "delete",
        )
        if get_confirmation("Confirm?"):
            for s3_key, _ in file_list:
                print("delete: s3://%s/%s" % (s3.bucket_name, s3_key))
                s3.client.delete_object(
                    Bucket=s3.bucket_name, Key=s3_key,
                )


def find_all_version_files(
    client,
    bucket: str,
    path: str,
    file_list: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
    deletemark: bool = False,
) -> List[str]:
    """Find all files based on versions.

    This method is able to find all files even deleted files or just delete marker left overs.
    Use this method when needing to cleanly delete all files including their versions.

    :param client: boto3 client
    :type client: boto3.client
    :param bucket: bucket to walk
    :type bucket: str
    :param path: the folder path to walk, empty to walk from root
    :type path: str
    :param file_list: list of files that was walked, for recursive purpose, pass empty list in
    :type file_list: List[str], optional
    :param exclude: glob pattern to exclude
    :type exclude: List[str], optional
    :param include: glob pattern to include
    :type include: glob pattern to include
    :param deletemark: set to true if only want to find deletemark
    :type deletemark: bool, optional
    :return: return a list of file names including deleted file names with delete mark remained
    :rtype: List[str]
    """
    if file_list is None:
        file_list = []
    if exclude is None:
        exclude = []
    if include is None:
        include = []

    paginator = client.get_paginator("list_object_versions")
    for result in paginator.paginate(Bucket=bucket, Delimiter="/", Prefix=path):
        if result.get("CommonPrefixes") is not None:
            for subdir in result.get("CommonPrefixes"):
                file_list = find_all_version_files(
                    client, bucket, subdir.get("Prefix"), file_list, exclude, include
                )
        if not deletemark:
            for file in result.get("Versions", []):
                if exclude_file(exclude, include, file.get("Key")):
                    continue
                if file.get("Key") in file_list:
                    continue
                else:
                    file_list.append(file.get("Key"))
        for file in result.get("DeleteMarkers", []):
            if exclude_file(exclude, include, file.get("Key")):
                continue
            if file.get("Key") in file_list:
                continue
            else:
                file_list.append(file.get("Key"))
    return file_list
