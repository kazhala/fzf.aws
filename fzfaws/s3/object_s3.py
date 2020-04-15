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
from fzfaws.s3.helper.get_copy_args import get_copy_args
from fzfaws.s3.helper.walk_s3_folder import walk_s3_folder


def object_s3(profile=False, bucket=None, recursive=False, version=False, allversion=False,
              exclude=[], include=[], name=False, storage=False, encryption=False, metadata=False, tagging=False, acl=False):
    """update selected object settings

    Display a menu based on recursive and version requirement
    if name is true, only handle rename

    TODO: replace copy_object method with copy method
        https://github.com/boto/boto3/issues/1981#issuecomment-560067088

    Args:
        profile: string or bool, use a different profile for this operation
        bucket: string, the bucket or bucket path for upload destination
            format: bucketname or bucketname/path/ or bucketname/filename
        recursive: bool, change the settings recursivly
        version: bool, change the settings for versions of object
        allversion: bool, change the settings for all versions of an object
        exclude: list, list of glob pattern to exclude
        include: list, list of glob pattern to include
        name: bool, update name of the object (limit object selection to one object)
            Note: not compatible with other attributes setting
        storage: bool, update storage of the object (skip attribute selection)
        encryption: bool, update encryption method of the object (skip attribute selection)
        metadata: bool, update meta of the object (skip attribute selection)
        tagging: bool, update tags of the object (skip attribute selection)
        acl: bool, update acl of the object (skip attribute selection)
    Returns:
        None
    Raises:
        InvalidS3PathPattern: when the specified s3 path is invalid pattern
        NoSelectionMade: when the required fzf selection is empty
        SubprocessError: when the local file search got zero result from fzf(no selection in fzf)
    """

    if allversion:
        version = True

    s3 = S3(profile)
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
            print('(dryrun) rename: s3://%s/%s to s3://%s/%s' %
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
            print('(dryrun) rename: s3://%s/%s to s3://%s/%s with version %s' %
                  (s3.bucket_name, obj_version.get('Key'), s3.bucket_name, new_name, obj_version.get('VersionId')))
            if get_confirmation('Confirm?'):
                print('rename: s3://%s/%s to s3://%s/%s with version %s' %
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
                    obj_version.get('Key'), s3.bucket_name, s3.client, version_id=obj_version.get('VersionId')), ExtraArgs=copy_object_args)
                # remove the progress bar
                sys.stdout.write('\033[2K\033[1G')

    elif recursive:
        s3_args = S3Args(s3)
        s3_args.set_extra_args(storage, acl, metadata, encryption, tagging)
        # check if only tags or acl is being updated
        # this way it won't create extra versions on the object
        check_result = s3_args.check_tag_acl()

        file_list = walk_s3_folder(s3.client, s3.bucket_name, s3.bucket_path, s3.bucket_path, [
        ], exclude, include, 'object', s3.bucket_path, s3.bucket_name)
        if get_confirmation('Confirm?'):
            if check_result:
                for original_key, destination_key in file_list:
                    print('update: s3://%s/%s' %
                          (s3.bucket_name, original_key))
                    if check_result.get('Tags'):
                        s3.client.put_object_tagging(
                            Bucket=s3.bucket_name,
                            Key=original_key,
                            Tagging={
                                'TagSet': check_result.get('Tags')
                            }
                        )
                    if check_result.get('Grants'):
                        grant_args = {
                            'Bucket': s3.bucket_name,
                            'Key': original_key
                        }
                        grant_args.update(check_result.get('Grants'))
                        s3.client.put_object_acl(**grant_args)

            else:
                for original_key, destination_key in file_list:
                    print('update: s3://%s/%s' %
                          (s3.bucket_name, original_key))
                    # Note: this will create new version if version is enabled
                    copy_object_args = get_copy_args(
                        s3, original_key, s3_args, extra_args=True)
                    copy_source = {
                        'Bucket': s3.bucket_name,
                        'Key': original_key
                    }
                    s3.client.copy(copy_source, s3.bucket_name, original_key, Callback=S3Progress(
                        original_key, s3.bucket_name, s3.client), ExtraArgs=copy_object_args)
                    # remove the progress bar
                    sys.stdout.write('\033[2K\033[1G')

    elif version:
        obj_versions = s3.get_object_version(select_all=allversion)
        s3_args = S3Args(s3)
        s3_args.set_extra_args(storage, acl, metadata,
                               encryption, tagging, version=obj_versions)
        # check if only tags or acl is being updated
        # this way it won't create extra versions on the object
        check_result = s3_args.check_tag_acl()

        for obj_version in obj_versions:
            print('(dryrun) update: s3://%s/%s with version %s' %
                  (s3.bucket_name, obj_version.get('Key'), obj_version.get('VersionId')))
        if get_confirmation('Confirm?'):
            for obj_version in obj_versions:
                print('update: s3://%s/%s with version %s' %
                      (s3.bucket_name, obj_version.get('Key'), obj_version.get('VersionId')))
                if check_result:
                    if check_result.get('Tags'):
                        s3.client.put_object_tagging(
                            Bucket=s3.bucket_name,
                            Key=obj_version.get('Key'),
                            VersionId=obj_version.get('VersionId'),
                            Tagging={
                                'TagSet': check_result.get('Tags')
                            }
                        )
                    if check_result.get('Grants'):
                        grant_args = {
                            'Bucket': s3.bucket_name,
                            'Key': obj_version.get('Key'),
                            'VersionId': obj_version.get('VersionId')
                        }
                        grant_args.update(check_result.get('Grants'))
                        s3.client.put_object_acl(**grant_args)
                else:
                    print('Nothing to update')

    else:
        s3_args = S3Args(s3)
        s3_args.set_extra_args(storage, acl, metadata, encryption, tagging)
        # check if only tags or acl is being updated
        # this way it won't create extra versions on the object
        check_result = s3_args.check_tag_acl()

        for s3_key in s3.path_list:
            print('(dryrun) update: s3://%s/%s' % (s3.bucket_name, s3_key))
        if get_confirmation('Confirm?'):
            for s3_key in s3.path_list:
                print('update: s3://%s/%s' % (s3.bucket_name, s3_key))
                if check_result:
                    if check_result.get('Tags'):
                        s3.client.put_object_tagging(
                            Bucket=s3.bucket_name,
                            Key=s3_key,
                            Tagging={
                                'TagSet': check_result.get('Tags')
                            }
                        )
                    if check_result.get('Grants'):
                        grant_args = {
                            'Bucket': s3.bucket_name,
                            'Key': s3_key
                        }
                        grant_args.update(check_result.get('Grants'))
                        s3.client.put_object_acl(**grant_args)

                else:
                    # Note: this will create new version if version is enabled
                    copy_object_args = get_copy_args(
                        s3, s3_key, s3_args, extra_args=True)
                    copy_source = {
                        'Bucket': s3.bucket_name,
                        'Key': s3_key
                    }
                    s3.client.copy(copy_source, s3.bucket_name, s3_key, Callback=S3Progress(
                        s3_key, s3.bucket_name, s3.client), ExtraArgs=copy_object_args)
                    # remove the progress bar
                    sys.stdout.write('\033[2K\033[1G')
