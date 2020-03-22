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
            if not recursive or version:
                s3.set_s3_object(version=version)
            else:
                s3.set_s3_path()
    else:
        s3.set_s3_bucket()
        if not recursive or version:
            s3.set_s3_object(version=version)
        else:
            s3.set_s3_path()

    if version:
        version_ids = s3.get_object_version(delete=True, select_all=allversion)
        for version_id in version_ids:
            print('(dryrun) delete: s3://%s/%s with version %s' %
                  (s3.bucket_name, s3.bucket_path, version_id))
        if get_confirmation('Confirm?'):
            for version_id in version_ids:
                print('delete: s3://%s/%s with version %s' %
                      (s3.bucket_name, s3.bucket_path, version_id))
                s3.client.delete_object(
                    Bucket=s3.bucket_name,
                    Key=s3.bucket_path,
                    MFA=mfa,
                    VersionId=version_id
                )
    elif recursive:
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
    else:
        # due the fact without recursive flag s3.bucket_path is set by s3.set_s3_object
        # the bucket_path is the valid s3 key so we don't need to call s3.get_s3_destination_key
        print('(dryrun) delete: s3://%s/%s' %
              (s3.bucket_name, s3.bucket_path))
        if get_confirmation('Confirm?'):
            print('delete: s3://%s/%s' %
                  (s3.bucket_name, s3.bucket_path))
            s3.client.delete_object(
                Bucket=s3.bucket_name,
                Key=s3.bucket_path,
            )
