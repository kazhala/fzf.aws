"""object settings and attributes update

update settings on s3 object
"""
import sys
from fzfaws.s3.s3 import S3
from fzfaws.s3.helper.s3args import S3Args
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.util import get_confirmation
from fzfaws.s3.helper.s3progress import S3Progress


def object_s3(bucket=None, recursive=False, version=False, allversion=False, exclude=[], include=[], name=False):
    """update selected object settings

    Display a menu based on recursive and version requirement
    if name is true, only handle rename

    TODO: replace copy_object method with copy method
        https://github.com/boto/boto3/issues/1981#issuecomment-560067088

    Args:
        bucket: string, the bucket or bucket path for upload destination
            format: bucketname or bucketname/path/ or bucketname/filename
        recursive: bool, change the settings recursivly
        version: bool, change the settings for versions of object
        allversion: bool, change the settings for all versions of an object
        exclude: list, list of glob pattern to exclude
        include: list, list of glob pattern to include
        name: bool, update name of the object (limit object selection to one object)
    Returns:
        None
    Raises:
        InvalidS3PathPattern: when the specified s3 path is invalid pattern
        NoSelectionMade: when the required fzf selection is empty
        SubprocessError: when the local file search got zero result from fzf(no selection in fzf)
    """

    s3 = S3()
    s3.set_bucket_and_path(bucket)
    if not s3.bucket_name:
        s3.set_s3_bucket()
    if recursive and not s3.bucket_path:
        s3.set_s3_path()
    elif name and not s3.bucket_path:
        s3.set_s3_object(version)
    elif not s3.path_list:
        s3.set_s3_object(version, multi_select=True)

    # fzf for the menu
    fzf = Pyfzf()
    fzf.append_fzf('StorageClass\n')
    fzf.append_fzf('ACL\n')
    fzf.append_fzf('Encryption\n')
    fzf.append_fzf('Metadata\n')
    fzf.append_fzf('Tagging\n')

    # handle rename
    if name:
        print('Enter the new name below (format: newname or path/newname for a new path)')
        new_name = input('Name(Orignal: %s): ' % s3.bucket_path)
        if not version:
            print('(dryrun) rename s3://%s/%s to s3://%s/%s' %
                  (s3.bucket_name, s3.bucket_path, s3.bucket_name, new_name))
            if get_confirmation('Confirm?'):
                print('rename: s3://%s/%s to s3://%s/%s' %
                      (s3.bucket_name, s3.bucket_path, s3.bucket_name, new_name))
                copy_source = {
                    'Bucket': s3.bucket_name,
                    'Key': s3.bucket_path,
                }
                s3.client.copy(copy_source, s3.bucket_name, new_name, Callback=S3Progress(
                    s3.bucket_path, s3.bucket_name, s3.client))
                # remove the progress bar
                sys.stdout.write('\033[2K\033[1G')
                s3.client.delete_object(
                    Bucket=s3.bucket_name,
                    Key=s3.bucket_path,
                )
        else:
            # get version
            obj_version = s3.get_object_version(key=s3.bucket_path)[0]
            print('(dryrun) rename s3://%s/%s to s3://%s/%s with version %s' %
                  (s3.bucket_name, obj_version.get('Key'), s3.bucket_name, new_name, obj_version.get('VersionId')))
            if get_confirmation('Confirm?'):
                print('rename s3://%s/%s to s3://%s/%s with version %s' %
                      (s3.bucket_name, obj_version.get('Key'), s3.bucket_name, new_name, obj_version.get('VersionId')))
                copy_source = {
                    'Bucket': s3.bucket_name,
                    'Key': obj_version.get('Key'),
                    'VersionId': obj_version.get('VersionId')
                }
                s3.client.copy(copy_source, s3.bucket_name, new_name, Callback=S3Progress(
                    obj_version.get('Key'), s3.bucket_name, s3.client, version_id=obj_version.get('VersionId')))
                # remove the progress bar
                sys.stdout.write('\033[2K\033[1G')

    elif recursive:
        pass
    elif version:
        pass
    else:
        s3_args = S3Args(s3)
        print('Select attributes to update on the selected objects')
        attributes = fzf.execute_fzf(print_col=1, multi_select=True)
        for attribute in attributes:
            if attribute == 'StorageClass':
                s3_args.set_storageclass()
            elif attribute == 'ACL':
                s3_args.set_ACL()
            elif attribute == 'Metadata':
                s3_args.set_metadata()
            elif attribute == 'Encryption':
                s3_args.set_encryption()
            elif attribute == 'Tagging':
                s3_args.set_tags()
        for s3_key in s3.path_list:
            print('(dryrun) update s3://%s/%s' % (s3.bucket_name, s3_key))
        if get_confirmation('Confirm?'):
            print('update s3://%s/%s' % (s3.bucket_name, s3_key))
            copy_object_args = {
                "Bucket": s3.bucket_name,
                "Key": s3_key,
                "CopySource": {
                    'Bucket': s3.bucket_name,
                    'Key': s3_key
                },
                "ACL": s3_args.acl,
                "GrantFullControl": s3_args.acl_full,
                "GrantRead": s3_args.acl_read,
                "GrantReadACP": s3_args.acl_acp_read,
                "GrantWriteACP": s3_args.acl_acp_write,
                "Metadata": s3_args.metadata,
            }
            if s3_args.storage_class:
                copy_object_args['StorageClass'] = s3_args.storage_class
            if s3_args.encryption:
                copy_object_args['ServerSideEncryption'] = s3_args.encryption
            if s3_args.encryption == 'aws:kms':
                copy_object_args['SSEKMSKeyId'] = s3_args.kms_id
            if s3_args.tags:
                copy_object_args['TaggingDirective'] = 'REPLACE'
                copy_object_args['Tagging'] = s3_args.tags
            else:
                copy_object_args['TaggingDirective'] = 'COPY'
            print(copy_object_args)
            for s3_key in s3.path_list:
                s3.client.copy_object(**copy_object_args)
