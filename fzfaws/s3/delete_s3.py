"""contains function for handling delete operation on s3

delete files/folders on s3
"""
from fzfaws.s3.s3 import S3
from fzfaws.s3.helper.walk_s3_folder import walk_s3_folder
from fzfaws.utils.util import get_confirmation


def delete_s3(path=None, recursive=False, exclude=[], include=[], mfa='', version=False, allversion=False):
    """delete file/directory on the selected s3 bucket

    Args:
        path: string, s3 bucket path, specify to skip bucket selection
            format: bucket/pathname or just bucket/
        recursive: bool, operate recursivly, set to true when deleting folders
        exclude: list, list of glob pattern to exclude
        include: list, list of glob pattern to include after exclude
        mfa: string, mfa serial number(arn from aws) and code seperate by a string
            only used for mfa and version enabled object
        version: bool, pick version/versions to delete
        allversion: bool, skip selection of version, delete all versions
    Returns:
        None
    Exceptions:
        InvalidS3PathPattern: when the path varibale is not a valid pattern
        bucket/ or bucket/pathname
    """

    s3 = S3()

    if allversion:
        version = True

    if path:
        s3.set_bucket_and_path(path)
        if not s3.bucket_path:
            if recursive:
                s3.set_s3_path()
            else:
                s3.set_s3_object(version=version, multi_select=True)
    else:
        s3.set_s3_bucket()
        if recursive:
            s3.set_s3_path()
        else:
            s3.set_s3_object(version=version, multi_select=True)

    if recursive:
        file_list = walk_s3_folder(s3.client, s3.bucket_name, s3.bucket_path, s3.bucket_path, [
        ], exclude, include, 'delete')
        if allversion:
            # loop through all files and request their versions
            if get_confirmation('Delete all files and all of their versions?'):
                for s3_key, destname in file_list:
                    version_ids = s3.get_object_version(
                        key=s3_key, delete=True, select_all=True)
                    for version_id in version_ids:
                        print('delete: s3://%s/%s with version %s' %
                              (s3.bucket_name, s3_key, version_id))
                        s3.client.delete_object(
                            Bucket=s3.bucket_name,
                            Key=s3_key,
                            MFA=mfa,
                            VersionId=version_id
                        )
        else:
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
        versions = s3.get_object_version(delete=True, select_all=allversion)
        for version in versions:
            print('(dryrun) delete: s3://%s/%s with version %s' %
                  (s3.bucket_name, version.get('Key'), version.get('VersionId')))
        if get_confirmation('Confirm?'):
            for version in versions:
                print('delete: s3://%s/%s with version %s' %
                      (s3.bucket_name, version.get('Key'), version.get('VersionId')))
                s3.client.delete_object(
                    Bucket=s3.bucket_name,
                    Key=version.get('Key'),
                    MFA=mfa,
                    VersionId=version.get('VersionId')
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
