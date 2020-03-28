"""object settings and attributes update

update settings on s3 object
"""
import sys
import json
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
                # initialise empty s3_args so that get_copy_args will use all the original value
                s3_args = S3Args(s3)
                copy_object_args = get_copy_args(
                    s3, s3.bucket_path, s3_args, extra_args=True)
                copy_source = {
                    'Bucket': s3.bucket_name,
                    'Key': s3.bucket_path,
                }
                s3.client.copy(copy_source, s3.bucket_name, new_name, Callback=S3Progress(
                    s3.bucket_path, s3.bucket_name, s3.client), ExtraArgs=copy_object_args)
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
                # initialise empty s3_args so that get_copy_args will use all the original value
                s3_args = S3Args(s3)
                copy_object_args = get_copy_args(
                    s3, s3.bucket_path, s3_args, extra_args=True, version=obj_version.get('VersionId'))
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
        s3_args.set_extra_args()

        for s3_key in s3.path_list:
            print('(dryrun) update s3://%s/%s' % (s3.bucket_name, s3_key))
        if get_confirmation('Confirm?'):
            for s3_key in s3.path_list:
                print('update s3://%s/%s' % (s3.bucket_name, s3_key))
                copy_object_args = get_copy_args(s3, s3_key, s3_args)
                s3.client.copy_object(**copy_object_args)


def get_copy_args(s3, s3_key, s3_args, extra_args=False, version=None):
    """get copy argument

    Args:
        s3: object, s3 instance of S3 class
        s3_key: string, the current object key on s3
        s3_args: object, args instance of S3Args
        extra_args: bool, is it for extra_args or full args
        version: bool, if current copy is for versioned copy
    Returns:
        copy_object_args: dict, the key ward argument for s3.client.copy_object
    """
    if not version:
        s3_obj = s3.resource.Object(s3.bucket_name, s3_key)
        s3_acl = s3.resource.ObjectAcl(s3.bucket_name, s3_key)
    else:
        s3_obj = s3.client.get_object(
            Bucket=s3.bucket_name,
            Key=s3_key,
            VersionId=version
        )
        s3_obj.pop('ResponseMetadata')
        s3_acl = s3.client.get_object_acl(
            Bucket=s3.bucket_name,
            Key=s3_key,
            VersionId=version,
        )
        exit()

    permission_read = []
    permission_acp_read = []
    permission_acp_write = []
    permission_full = []
    for grantee in s3_acl.grants:
        if grantee.get('Permission') == 'READ':
            if grantee['Grantee'].get('ID'):
                permission_read.append(
                    'id=' + grantee['Grantee']['ID'])
            elif grantee['Grantee'].get('URI'):
                permission_read.append(
                    'uri=' + grantee['Grantee']['URI'])
        elif grantee['Grantee'].get('Permission') == 'FULL_CONTROL':
            if grantee['Grantee'].get('ID'):
                permission_full.append(
                    'id=' + grantee['Grantee']['ID'])
            elif grantee['Grantee'].get('URI'):
                permission_full.append(
                    'uri=' + grantee['Grantee']['URI'])
        elif grantee.get('Permission') == 'WRITE_ACP':
            if grantee['Grantee'].get('ID'):
                permission_acp_write.append(
                    'id=' + grantee['Grantee']['ID'])
            elif grantee['Grantee'].get('URI'):
                permission_acp_write.append(
                    'uri=' + grantee['Grantee']['URI'])
        elif grantee.get('Permission') == 'READ_ACP':
            if grantee['Grantee'].get('ID'):
                permission_acp_read.append(
                    'id=' + grantee['Grantee']['ID'])
            elif grantee['Grantee'].get('URI'):
                permission_acp_read.append(
                    'uri=' + grantee['Grantee']['URI'])

    if not extra_args:
        copy_object_args = {
            "Bucket": s3.bucket_name,
            "Key": s3_key,
            "CopySource": {
                'Bucket': s3.bucket_name,
                'Key': s3_key
            },
        }
    else:
        copy_object_args = {}

    if s3_args.storage_class:
        copy_object_args['StorageClass'] = s3_args.storage_class
    elif s3_obj.storage_class:
        copy_object_args['StorageClass'] = s3_obj.storage_class

    if s3_args.encryption:
        if s3_args.encryption != 'None':
            copy_object_args['ServerSideEncryption'] = s3_args.encryption
    elif s3_obj.server_side_encryption:
        copy_object_args['ServerSideEncryption'] = s3_obj.server_side_encryption

    if s3_args.encryption and s3_args.encryption == 'aws:kms':
        copy_object_args['SSEKMSKeyId'] = s3_args.kms_id
    elif s3_obj.server_side_encryption and s3_obj.server_side_encryption == 'aws:kms':
        copy_object_args['SSEKMSKeyId'] = s3_obj.ssekms_key_id

    if s3_args.tags:
        copy_object_args['TaggingDirective'] = 'REPLACE'
        copy_object_args['Tagging'] = s3_args.tags

    if s3_args.metadata:
        copy_object_args['Metadata'] = s3_args.metadata
        copy_object_args['MetadataDirective'] = 'REPLACE'

    if s3_args.acl:
        copy_object_args['ACL'] = s3_args.acl
    else:
        if s3_args.acl_full:
            copy_object_args['GrantFullControl'] = s3_args.acl_full
        elif permission_full:
            copy_object_args['GrantFullControl'] = ','.join(
                permission_full)

        if s3_args.acl_read:
            copy_object_args['GrantRead'] = s3_args.acl_read
        elif permission_read:
            copy_object_args['GrantRead'] = ','.join(
                permission_read)

        if s3_args.acl_acp_read:
            copy_object_args['GrantReadACP'] = s3_args.acl_acp_read
        elif permission_acp_read:
            copy_object_args['GrantReadACP'] = ','.join(
                permission_acp_read)

        if s3_args.acl_acp_write:
            copy_object_args['GrantWriteACP'] = s3_args.acl_acp_write
        elif permission_acp_write:
            copy_object_args['GrantWriteACP'] = ','.join(
                permission_acp_write)
    return copy_object_args
