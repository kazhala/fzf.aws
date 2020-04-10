"""bucket transfer operation

contains the main function for moving object between buckets
"""
import os
import sys
import re
from botocore.exceptions import ClientError
from fzfaws.s3.s3 import S3
from fzfaws.s3.helper.sync_s3 import sync_s3
from fzfaws.s3.helper.walk_s3_folder import walk_s3_folder
from fzfaws.utils.util import get_confirmation
from fzfaws.s3.helper.s3progress import S3Progress
from fzfaws.s3.helper.s3args import S3Args
from fzfaws.s3.helper.get_copy_args import get_copy_args


def bucket_s3(profile=False, from_bucket=None, to_bucket=None, recursive=False, sync=False, exclude=[], include=[], version=False, preserve=False):
    """transfer file between buckts

    handle transfer file between buckets or even within the same bucket
    Handle glob pattern through exclude list first than it will process the include to explicit include files

    Args:
        profile: string or bool, use a different profile for operation
        from_bucket: string, target bucket path
        to_bucket: string, destination bucket path
        recursive: bool, whether to copy entire folder or just file
        sync: bool, use sync operation through subprocess
        exclude: list, list of glob pattern to exclude
        include: list, list of glob pattern to include afer exclude
        version: bool, transfer file with specific version
        preserve: bool, preserve previous object details like storage class encryption etc
    Return:
        None
    Raises:
        InvalidS3PathPattern: when the specified s3 path is invalid pattern
        NoSelectionMade: when the required fzf selection did not receive any result
    """

    s3 = S3(profile)

    # initialise variables to avoid directly using s3 instance since processing 2 buckets
    target_bucket = None
    target_path = ''
    target_path_list = []
    dest_bucket = None
    dest_path = ''

    search_folder = True if recursive or sync else False

    if from_bucket:
        target_bucket, target_path, target_path_list = process_path_param(
            from_bucket, s3, search_folder, version=version)
        if version:
            obj_versions = s3.get_object_version()
        # clean up the s3 attributes for next operation
        s3.bucket_name = None
        s3.bucket_path = ''
        if to_bucket:
            dest_bucket, dest_path, dest_path_list = process_path_param(
                to_bucket, s3, True)
        else:
            s3.set_s3_bucket(
                header='Set the destination bucket where the file should be transfered')
            s3.set_s3_path()
            dest_bucket = s3.bucket_name
            dest_path = s3.bucket_path

    else:
        s3.set_s3_bucket(
            header='Set the target bucket which contains the file to transfer')
        target_bucket = s3.bucket_name
        if search_folder:
            s3.set_s3_path()
            target_path = s3.bucket_path
        else:
            s3.set_s3_object(multi_select=True, version=version)
            target_path_list = s3.path_list

        if version:
            obj_versions = s3.get_object_version()

        # clean up the s3 attributes for next operation
        s3.bucket_name = None
        s3.bucket_path = ''
        s3.set_s3_bucket(
            header='Set the destination bucket where the file should be transfered')
        s3.set_s3_path()
        dest_bucket = s3.bucket_name
        dest_path = s3.bucket_path

    if sync:
        sync_s3(exclude, include, 's3://%s/%s' % (target_bucket,
                                                  target_path), 's3://%s/%s' % (dest_bucket, dest_path))
    elif recursive:
        file_list = walk_s3_folder(s3.client, target_bucket, target_path, target_path, [
        ], exclude, include, 'bucket', dest_path, dest_bucket)
        if get_confirmation('Confirm?'):
            for s3_key, dest_pathname in file_list:
                print('copy: s3://%s/%s to s3://%s/%s' %
                      (target_bucket, s3_key, dest_bucket, dest_pathname))
                copy_source = {
                    'Bucket': target_bucket,
                    'Key': s3_key
                }
                if not preserve:
                    s3.client.copy(copy_source, dest_bucket, dest_pathname, Callback=S3Progress(
                        s3_key, target_bucket, s3.client))
                    # remove the progress bar
                    sys.stdout.write('\033[2K\033[1G')
                else:
                    s3.bucket_name = target_bucket
                    copy_and_preserve(s3, target_bucket, s3_key,
                                      dest_bucket, dest_pathname)

    elif version:
        # set s3 attributes for getting destination key
        s3.bucket_name = dest_bucket
        s3.bucket_path = dest_path
        for obj_version in obj_versions:
            s3_key = s3.get_s3_destination_key(obj_version.get('Key'))
            print('(dryrun) copy: s3://%s/%s to s3://%s/%s with version %s' %
                  (target_bucket, obj_version.get('Key'), dest_bucket, s3_key, obj_version.get('VersionId')))
        if get_confirmation('Confirm?'):
            for obj_version in obj_versions:
                s3_key = s3.get_s3_destination_key(obj_version.get('Key'))
                print('copy: s3://%s/%s to s3://%s/%s with version %s' %
                      (target_bucket, obj_version.get('Key'), dest_bucket, s3_key, obj_version.get('VersionId')))
                copy_source = {
                    'Bucket': target_bucket,
                    'Key': obj_version.get('Key'),
                    'VersionId': obj_version.get('VersionId')
                }
                if not preserve:
                    s3.client.copy(copy_source, dest_bucket, s3_key, Callback=S3Progress(obj_version.get(
                        'Key'), target_bucket, s3.client, version_id=obj_version.get('VersionId')))
                    # remove the progress bar
                    sys.stdout.write('\033[2K\033[1G')
                else:
                    s3.bucket_name = target_bucket
                    copy_and_preserve(s3, target_bucket, obj_version.get(
                        'Key'), dest_bucket, s3_key, version=obj_version.get('VersionId'))

    else:
        # set the s3 instance name and path the destination bucket
        s3.bucket_name = dest_bucket
        s3.bucket_path = dest_path
        for target_path in target_path_list:
            # process the target key path and get the destination key path
            s3_key = s3.get_s3_destination_key(target_path)
            print('(dryrun) copy: s3://%s/%s to s3://%s/%s' %
                  (target_bucket, target_path, dest_bucket, s3_key))
        if get_confirmation('Confirm?'):
            for target_path in target_path_list:
                s3_key = s3.get_s3_destination_key(target_path)
                print('copy: s3://%s/%s to s3://%s/%s' %
                      (target_bucket, target_path, dest_bucket, s3_key))
                copy_source = {
                    'Bucket': target_bucket,
                    'Key': target_path
                }
                if not preserve:
                    s3.client.copy(copy_source, dest_bucket, s3_key, Callback=S3Progress(
                        target_path, target_bucket, s3.client))
                    # remove the progress bar
                    sys.stdout.write('\033[2K\033[1G')
                else:
                    s3.bucket_name = target_bucket
                    copy_and_preserve(s3, target_bucket,
                                      target_path, dest_bucket, s3_key)


def copy_and_preserve(s3, target_bucket, target_path, dest_bucket, dest_path, version=None):
    """copy object to other buckets but preserve details

    Args:
        s3: object, S3 instance, make sure to set s3.bucket_name
        target_bucket: string, bucket which contains the file to move
        target_path: string, the file to move
        dest_bucket: string, destination bucket
        dest_path: string, destination file path
        version: string, versionId of the object
    Returns:
        None
    Exceptions:
        ClientError: when moving encrypted object with kms over regions
    """
    copy_source = {
        'Bucket': target_bucket,
        'Key': target_path
    }
    if version:
        copy_source['VersionId'] = version
    s3_args = S3Args(s3)
    copy_object_args = get_copy_args(
        s3, target_path, s3_args, extra_args=True, version=version)

    while True:
        try:
            s3.client.copy(copy_source, dest_bucket, dest_path, Callback=S3Progress(
                target_path, s3.bucket_name, s3.client), ExtraArgs=copy_object_args)
            # remove the progress bar
            sys.stdout.write('\033[2K\033[1G')
            break
        except ClientError as e:
            error_pattern = r'^.*\((.*)\).*$'
            error_name = re.match(error_pattern, str(e)).group(1)
            if error_name == 'AccessDenied':
                print(80*'-')
                print(e)
                print('You may have ACL policies that enable public access but '
                      'the destination bucket is blocking all public access, ' +
                      "you need to either uncheck 'block all public access' or update your object ACL settings " +
                      "or try again without the -p flag or continue without preserving the ACL")
                if not get_confirmation('Continue without preserving ACL?'):
                    raise
                copy_object_args.pop('GrantFullControl', None)
                copy_object_args.pop('GrantRead', None)
                copy_object_args.pop('GrantReadACP', None)
                copy_object_args.pop('GrantWriteACP', None)
            # # handle when kms encrypt object move to a bucket in different region
            elif error_name == 'KMS.NotFoundException':
                copy_object_args['ServerSideEncryption'] = 'AES256'
                copy_object_args.pop('SSEKMSKeyId', None)
            else:
                raise


def process_path_param(bucket, s3, search_folder, version=False):
    """process bucket parameter and return bucket name and path

    Args:
        bucket: string, raw bucket parameter from the argument
        s3: object, s3 instance from the S3 class
        search_folder: bool, search folder or file
    Returns:
        A tuple consisting of the bucketname and bucket path
    """
    s3.set_bucket_and_path(bucket)
    if not s3.bucket_path:
        if search_folder:
            s3.set_s3_path()
        else:
            s3.set_s3_object(multi_select=True, version=version)
    return (s3.bucket_name, s3.bucket_path, s3.path_list)
