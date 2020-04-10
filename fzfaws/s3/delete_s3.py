"""contains function for handling delete operation on s3

delete files/folders on s3
"""
from fzfaws.s3.s3 import S3
from fzfaws.s3.helper.walk_s3_folder import walk_s3_folder
from fzfaws.utils.util import get_confirmation
from fzfaws.s3.helper.exclude_file import exclude_file


def delete_s3(profile=False, bucket=None, recursive=False, exclude=[], include=[], mfa='', version=False, allversion=False, deletemark=False, clean=False):
    """delete file/directory on the selected s3 bucket

    Args:
        profile: string or bool, use a different profile for operation
        bucket: string, s3 bucket path, specify to skip bucket selection
            format: bucket/pathname or just bucket/
        recursive: bool, operate recursivly, set to true when deleting folders
        exclude: list, list of glob pattern to exclude
        include: list, list of glob pattern to include after exclude
        mfa: string, mfa serial number(arn from aws) and code seperate by a string
            only used for mfa and version enabled object
        version: bool, pick version/versions to delete
        allversion: bool, skip selection of version, delete all versions
        deletemark: bool, only display files with deletemark
        clean: bool, recursivly delete all olderversions but leave the current version
    Returns:
        None
    Raises:
        InvalidS3PathPattern: when the path varibale is not a valid pattern
            bucket/ or bucket/pathname
        NoSelectionMade: when the required fzf selection did not receive any result
    """

    s3 = S3(profile)

    if deletemark:
        version = True
    if allversion:
        version = True
        recursive = True
    if clean:
        version = True
        allversion = True
        recursive = True

    s3.set_bucket_and_path(bucket)
    if not s3.bucket_name:
        s3.set_s3_bucket()
    if recursive:
        if not s3.bucket_path:
            s3.set_s3_path()
    else:
        if not s3.path_list:
            s3.set_s3_object(version=version, multi_select=True,
                             deletemark=deletemark)

    if recursive:
        if allversion:
            # use a different method other than the walk s3 folder
            # since walk_s3_folder doesn't provide access to deleted version object
            # delete_all_versions method will list all files including deleted versions or even delete marker
            file_list = find_all_version_files(
                s3.client, s3.bucket_name, s3.bucket_path, [], exclude, include, deletemark)
            obj_versions = []
            # loop through all files and get their versions
            for file in file_list:
                obj_versions.extend(s3.get_object_version(
                    key=file, delete=True, select_all=True, non_current=clean))
                print('(dryrun) delete: s3://%s/%s and all %s' %
                      (s3.bucket_name, file, 'versions' if not clean else 'non-current versions'))
            if get_confirmation('Delete %s?' % ('all of their versions' if not clean else 'all non-current versions')):
                for obj_version in obj_versions:
                    print('delete: s3://%s/%s with version %s' %
                          (s3.bucket_name, obj_version.get('Key'), obj_version.get('VersionId')))
                    s3.client.delete_object(
                        Bucket=s3.bucket_name,
                        Key=obj_version.get('Key'),
                        MFA=mfa,
                        VersionId=obj_version.get('VersionId')
                    )

        else:
            file_list = walk_s3_folder(s3.client, s3.bucket_name, s3.bucket_path, s3.bucket_path, [
            ], exclude, include, 'delete')
            if get_confirmation('Confirm?'):
                # destiname here is completely useless, only for looping purpose
                for s3_key, destname in file_list:
                    print('delete: s3://%s/%s' %
                          (s3.bucket_name, s3_key))
                    s3.client.delete_object(
                        Bucket=s3.bucket_name,
                        Key=s3_key,
                    )

    elif version:
        obj_versions = s3.get_object_version(
            delete=True, select_all=allversion)
        for obj_version in obj_versions:
            print('(dryrun) delete: s3://%s/%s with version %s' %
                  (s3.bucket_name, obj_version.get('Key'), obj_version.get('VersionId')))
        if get_confirmation('Confirm?'):
            for obj_version in obj_versions:
                print('delete: s3://%s/%s with version %s' %
                      (s3.bucket_name, obj_version.get('Key'), obj_version.get('VersionId')))
                s3.client.delete_object(
                    Bucket=s3.bucket_name,
                    Key=obj_version.get('Key'),
                    MFA=mfa,
                    VersionId=obj_version.get('VersionId')
                )

    else:
        # due the fact without recursive flag s3.bucket_path is set by s3.set_s3_object
        # the bucket_path is the valid s3 key so we don't need to call s3.get_s3_destination_key
        for s3_path in s3.path_list:
            print('(dryrun) delete: s3://%s/%s' %
                  (s3.bucket_name, s3_path))
        if get_confirmation('Confirm?'):
            for s3_path in s3.path_list:
                print('delete: s3://%s/%s' %
                      (s3.bucket_name, s3_path))
                s3.client.delete_object(
                    Bucket=s3.bucket_name,
                    Key=s3_path,
                )


def find_all_version_files(client, bucket, path, file_list=[], exclude=[], include=[], deletemark=False):
    """find all files based on versions

    This method is able to find all files even deleted files or just delete marker left overs
    Use this method when needing to cleanly delete all files including their versions

    Args:
        client: object, boto3 s3 client
        bucket: string, name of the bucket
        path: string, the folder to delete all files, empty for root
        file_list: list, the return file list
        exclude: list, list of pattern to exclude
        include: list, list of pattern to include after exclude
        deletemark: bool, set to True if only want to find file with deletemark
    Returns:
        file_list: list, list of file names including deleted file names with delete marker remained
    """

    paginator = client.get_paginator('list_object_versions')
    for result in paginator.paginate(Bucket=bucket, Delimiter='/', Prefix=path):
        if result.get('CommonPrefixes') is not None:
            for subdir in result.get('CommonPrefixes'):
                file_list = find_all_version_files(client, bucket, subdir.get(
                    'Prefix'), file_list, exclude, include)
        if not deletemark:
            for file in result.get('Versions', []):
                if exclude_file(exclude, include, file.get('Key')):
                    continue
                if file.get('Key') in file_list:
                    continue
                else:
                    file_list.append(file.get('Key'))
        for file in result.get('DeleteMarkers', []):
            if exclude_file(exclude, include, file.get('Key')):
                continue
            if file.get('Key') in file_list:
                continue
            else:
                file_list.append(file.get('Key'))
    return file_list
