"""process the s3 folder for handling recusive operation on s3

handle the filter and listing of s3 folder
"""
import os
from fzfaws.s3.helper.exclude_file import exclude_file


def walk_s3_folder(client, bucket, bucket_path, root='', file_list=[], exclude=[], include=[], operation='download', destination_path='/', destination_bucket=''):
    """download directory from s3 recursivly

    reference: https://stackoverflow.com/a/33350380
    recursivly call walk_s3_folder to reach the bottom level and append the file path
    to the file_list

    process the destination when root is not bucket root

    Args:
        client: boto3.client('s3')
        bucket: string, name of the bucket
        bucket_path: string, which path to download or the current recursive path
        root: string, the current operation root
            when calling walk_s3_folder(), set root to bucket_path
        file_list: list, accumulated list of file to download
        exclude: list, list of glob pattern to exclude
        include: list, list of glob pattern to include after exclude
        operation: string, current operation type
            Print different information based on operation type
            download/bucket/delete/object
        destination_path: string, the destination root path
        destination_bucket: string, the destination bucket name
            Only set this for operation='bucket'
    Returns:
        file_list: return the list of file to download. The loop contains a tuple
        that coould be iterate over
    """

    paginator = client.get_paginator('list_objects')
    for result in paginator.paginate(Bucket=bucket, Delimiter='/', Prefix=bucket_path):
        if result.get('CommonPrefixes') is not None:
            for subdir in result.get('CommonPrefixes'):
                file_list = walk_s3_folder(client, bucket, subdir.get(
                    'Prefix'), root, file_list, exclude, include, operation, destination_path, destination_bucket)
        for file in result.get('Contents', []):
            if file.get('Key').endswith('/') or not file.get('Key'):
                # user created dir in S3 console will appear in the result and is not downloadable
                continue
            if exclude_file(exclude, include, file.get('Key')):
                continue
            if not root:
                dest_pathname = os.path.join(destination_path, file.get('Key'))
            else:
                # strip off the root if the root is not root of the bucket
                # with this, downloading sub folders like bucket/aws
                # will not create a folder called /aws in the target directory
                # rather, it will just download all files in bucket/aws to the target directory
                # nested folders within bucket/aws will still be created in the target directory
                # doing this because aws cli does it, do not want to change the behavior
                strip_root_path = '/'.join(file.get('Key').split('/')[1:])
                dest_pathname = os.path.join(destination_path, strip_root_path)
            if operation == 'download':
                print('(dryrun) download: s3://%s/%s to %s' %
                      (bucket, file.get('Key'), dest_pathname))
            elif operation == 'bucket':
                print('(dryrun) copy: s3://%s/%s to s3://%s/%s' %
                      (bucket, file.get('Key'), destination_bucket, dest_pathname))
            elif operation == 'delete':
                print('(dryrun) delete: s3://%s/%s' %
                      (bucket, file.get('Key')))
            elif operation == 'object':
                print('(dryrun) update: s3://%s/%s' %
                      (bucket, file.get('Key')))
            file_list.append((file.get('Key'), dest_pathname))
    return file_list
