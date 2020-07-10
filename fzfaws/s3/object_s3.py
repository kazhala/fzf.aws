"""Contains function to update s3 object attribute."""
from typing import List, Optional, Union

from fzfaws.s3 import S3
from fzfaws.s3.helper.get_copy_args import get_copy_args
from fzfaws.s3.helper.s3args import S3Args
from fzfaws.s3.helper.s3progress import S3Progress
from fzfaws.s3.helper.s3transferwrapper import S3TransferWrapper
from fzfaws.s3.helper.walk_s3_folder import walk_s3_folder
from fzfaws.utils import get_confirmation


def object_s3(
    profile: Union[str, bool] = False,
    bucket: str = None,
    recursive: bool = False,
    version: bool = False,
    allversion: bool = False,
    exclude: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
    name: bool = False,
    storage: bool = False,
    encryption: bool = False,
    metadata: bool = False,
    tagging: bool = False,
    acl: bool = False,
) -> None:
    """Update selected object settings.

    Display a menu based on recursive and version requirement.
    If name is true, only handle rename.

    :param profile: use a different profile for this operation
    :type profile: Union[str, bool], optional
    :param bucket: bucket name that contains the object
    :type bucket: str, optional
    :param recursive: recusive update object attr
    :type recursive: bool, optional
    :param allversion: update all versions of a object
    :type allversion: bool, optional
    :param exclude: glob pattern to exclude
    :type exclude: List[str], optional
    :param include: glob pattern to include
    :type include: List[str], optional
    :param name: update name
    :type name: bool, optional
    :param storage: update storage
    :type storage: bool, optional
    :param encryption: update encryption
    :type encryption: bool, optional
    :param metadata: update metadata
    :type metadata: bool, optional
    :param tagging: update tagging
    :type tagging: bool, optional
    :param acl: update acl
    :type acl: bool, optional
    """
    if exclude is None:
        exclude = []
    if include is None:
        include = []

    if allversion:
        version = True

    s3 = S3(profile)
    s3.set_bucket_and_path(bucket)
    if not s3.bucket_name:
        s3.set_s3_bucket()
    if recursive and not s3.path_list[0]:
        s3.set_s3_path()
    elif name and not s3.path_list[0]:
        s3.set_s3_object(version)
    elif not s3.path_list[0]:
        s3.set_s3_object(version, multi_select=True)

    # handle rename
    if name:
        update_object_name(s3, version)

    elif recursive:
        update_object_recursive(
            s3, storage, acl, metadata, encryption, tagging, exclude, include
        )

    elif version:
        update_object_version(s3, allversion, acl, tagging)

    else:
        # update single object
        s3_args = S3Args(s3)
        s3_args.set_extra_args(storage, acl, metadata, encryption, tagging)
        # check if only tags or acl is being updated
        # this way it won't create extra versions on the object, if versioning is enabled
        check_result = s3_args.check_tag_acl()

        for s3_key in s3.path_list:
            print("(dryrun) update: s3://%s/%s" % (s3.bucket_name, s3_key))
        if get_confirmation("Confirm?"):
            for s3_key in s3.path_list:
                print("update: s3://%s/%s" % (s3.bucket_name, s3_key))
                if check_result:
                    if check_result.get("Tags"):
                        s3.client.put_object_tagging(
                            Bucket=s3.bucket_name,
                            Key=s3_key,
                            Tagging={"TagSet": check_result.get("Tags")},
                        )
                    if check_result.get("Grants"):
                        grant_args = {"Bucket": s3.bucket_name, "Key": s3_key}
                        grant_args.update(check_result.get("Grants", {}))
                        s3.client.put_object_acl(**grant_args)

                else:
                    # Note: this will create new version if version is enabled
                    copy_object_args = get_copy_args(
                        s3, s3_key, s3_args, extra_args=True
                    )
                    copy_source = {"Bucket": s3.bucket_name, "Key": s3_key}
                    s3transferwrapper = S3TransferWrapper()
                    s3.client.copy(
                        copy_source,
                        s3.bucket_name,
                        s3_key,
                        Callback=S3Progress(s3_key, s3.bucket_name, s3.client),
                        ExtraArgs=copy_object_args,
                        Config=s3transferwrapper.transfer_config,
                    )


def update_object_version(
    s3: S3, allversion: bool = False, acl: bool = False, tagging: bool = False,
) -> None:
    """Update versions of object's attributes.

    Note: this operation only allow update of acl and tagging, because
    this won't introduce new objects.

    :param s3: S3 instance
    :type s3: S3
    :param allversion: update all versions?
    :type allversion: bool, optional
    :param acl: update acl
    :type acl: bool, optional
    :param tagging: update tagging
    :type tagging: bool, optional
    """
    obj_versions = s3.get_object_version(select_all=allversion)
    s3_args = S3Args(s3)
    s3_args.set_extra_args(acl, tagging, version=obj_versions)
    # check if only tags or acl is being updated
    # this way it won't create extra versions on the object
    check_result = s3_args.check_tag_acl()

    for obj_version in obj_versions:
        print(
            "(dryrun) update: s3://%s/%s with version %s"
            % (s3.bucket_name, obj_version.get("Key"), obj_version.get("VersionId"))
        )
    if get_confirmation("Confirm?"):
        for obj_version in obj_versions:
            print(
                "update: s3://%s/%s with version %s"
                % (
                    s3.bucket_name,
                    obj_version.get("Key"),
                    obj_version.get("VersionId"),
                )
            )
            if check_result:
                if check_result.get("Tags"):
                    s3.client.put_object_tagging(
                        Bucket=s3.bucket_name,
                        Key=obj_version.get("Key"),
                        VersionId=obj_version.get("VersionId"),
                        Tagging={"TagSet": check_result.get("Tags")},
                    )
                if check_result.get("Grants"):
                    grant_args = {
                        "Bucket": s3.bucket_name,
                        "Key": obj_version.get("Key"),
                        "VersionId": obj_version.get("VersionId"),
                    }
                    grant_args.update(check_result.get("Grants", {}))
                    s3.client.put_object_acl(**grant_args)
            else:
                print("Nothing to update")


def update_object_recursive(
    s3: S3,
    storage: bool = False,
    acl: bool = False,
    metadata: bool = False,
    encryption: bool = False,
    tagging: bool = False,
    exclude: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
) -> None:
    """Recusive update object attributes.

    :param s3: S3 class instance
    :type s3: S3
    :param storage: update storage
    :type storage: bool, optional
    :param acl: update acl
    :type acl: bool, optional
    :param metadata: update metadata
    :type metadata: bool, optional
    :param encryption: update encryption
    :type encryption: bool, optional
    :param tagging: update tagging
    :type tagging: bool, optional
    :param exclude: glob pattern to exclude
    :type exclude: List[str], optional
    :param include: glob pattern to include
    :type include: List[str], optional
    """
    if exclude is None:
        exclude = []
    if include is None:
        include = []

    s3_args = S3Args(s3)
    s3_args.set_extra_args(storage, acl, metadata, encryption, tagging)
    # check if only tags or acl is being updated
    # this way it won't create extra versions on the object
    check_result = s3_args.check_tag_acl()

    file_list = walk_s3_folder(
        s3.client,
        s3.bucket_name,
        s3.path_list[0],
        s3.path_list[0],
        [],
        exclude,
        include,
        "object",
        s3.path_list[0],
        s3.bucket_name,
    )
    if get_confirmation("Confirm?"):
        if check_result:
            for original_key, _ in file_list:
                print("update: s3://%s/%s" % (s3.bucket_name, original_key))
                if check_result.get("Tags"):
                    s3.client.put_object_tagging(
                        Bucket=s3.bucket_name,
                        Key=original_key,
                        Tagging={"TagSet": check_result.get("Tags")},
                    )
                if check_result.get("Grants"):
                    grant_args = {"Bucket": s3.bucket_name, "Key": original_key}
                    grant_args.update(check_result.get("Grants", {}))
                    s3.client.put_object_acl(**grant_args)

        else:
            for original_key, _ in file_list:
                print("update: s3://%s/%s" % (s3.bucket_name, original_key))
                # Note: this will create new version if version is enabled
                copy_object_args = get_copy_args(
                    s3, original_key, s3_args, extra_args=True
                )
                copy_source = {"Bucket": s3.bucket_name, "Key": original_key}
                s3transferwrapper = S3TransferWrapper()
                s3.client.copy(
                    copy_source,
                    s3.bucket_name,
                    original_key,
                    Callback=S3Progress(original_key, s3.bucket_name, s3.client),
                    ExtraArgs=copy_object_args,
                    Config=s3transferwrapper.transfer_config,
                )


def update_object_name(s3: S3, version: bool = False) -> None:
    """Update object name.

    :param s3: S3 class instance
    :type s3: S3
    :param version: whether to rename version's name, this will create a new object
    :type version: bool, optional
    """
    print("Enter the new name below (format: newname or path/newname for a new path)")
    new_name = input("Name(Orignal: %s): " % s3.path_list[0])

    if not version:
        print(
            "(dryrun) rename: s3://%s/%s to s3://%s/%s"
            % (s3.bucket_name, s3.path_list[0], s3.bucket_name, new_name)
        )
        if get_confirmation("Confirm?"):
            print(
                "rename: s3://%s/%s to s3://%s/%s"
                % (s3.bucket_name, s3.path_list[0], s3.bucket_name, new_name)
            )
            # initialise empty s3_args so that get_copy_args will use all the original value
            s3_args = S3Args(s3)
            copy_object_args = get_copy_args(
                s3, s3.path_list[0], s3_args, extra_args=True
            )
            copy_source = {
                "Bucket": s3.bucket_name,
                "Key": s3.path_list[0],
            }
            s3transferwrapper = S3TransferWrapper()
            s3.client.copy(
                copy_source,
                s3.bucket_name,
                new_name,
                Callback=S3Progress(s3.path_list[0], s3.bucket_name, s3.client),
                ExtraArgs=copy_object_args,
                Config=s3transferwrapper.transfer_config,
            )
            s3.client.delete_object(
                Bucket=s3.bucket_name, Key=s3.path_list[0],
            )

    else:
        # get version
        obj_version = s3.get_object_version(key=s3.path_list[0])[0]
        print(
            "(dryrun) rename: s3://%s/%s to s3://%s/%s with version %s"
            % (
                s3.bucket_name,
                obj_version.get("Key"),
                s3.bucket_name,
                new_name,
                obj_version.get("VersionId"),
            )
        )
        if get_confirmation("Confirm?"):
            print(
                "rename: s3://%s/%s to s3://%s/%s with version %s"
                % (
                    s3.bucket_name,
                    obj_version.get("Key"),
                    s3.bucket_name,
                    new_name,
                    obj_version.get("VersionId"),
                )
            )
            # initialise empty s3_args so that get_copy_args will use all the original value
            s3_args = S3Args(s3)
            copy_object_args = get_copy_args(
                s3,
                s3.path_list[0],
                s3_args,
                extra_args=True,
                version=obj_version.get("VersionId"),
            )
            copy_source = {
                "Bucket": s3.bucket_name,
                "Key": obj_version.get("Key"),
                "VersionId": obj_version.get("VersionId"),
            }
            s3transferwrapper = S3TransferWrapper()
            s3.client.copy(
                copy_source,
                s3.bucket_name,
                new_name,
                Callback=S3Progress(
                    obj_version.get("Key", ""),
                    s3.bucket_name,
                    s3.client,
                    version_id=obj_version.get("VersionId"),
                ),
                ExtraArgs=copy_object_args,
                Config=s3transferwrapper.transfer_config,
            )
