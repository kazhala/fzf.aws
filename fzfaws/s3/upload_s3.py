"""handles uploading operation of s3

upload local files/directories to s3
"""
import os
import sys
import fnmatch
import subprocess
from s3transfer import S3Transfer
from fzfaws.s3.s3 import S3
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.util import get_confirmation
from fzfaws.s3.helper.sync_s3 import sync_s3
from fzfaws.s3.helper.exclude_file import exclude_file
from fzfaws.s3.helper.s3progress import S3Progress


def upload_s3(path=None, local=[], recursive=False, hidden=False, root=False, sync=False, exclude=[], include=[]):
    """upload local files/directories to s3

    upload through boto3 s3 client
    glob pattern are handled first exclude list then will run the include list

    Args:
        path: string, s3 bucket path for upload destination
            formate: bucket/pathname
        local: list, list of local file to upload
        recursive: bool, upload directory
        hidden: bool, include hidden file during local file search
        root: bool, search local file from root
        sync: bool, use s3 cli sync operation
        exclude: list, list of glob pattern to exclude
        include: list, list of glob pattern to include after exclude
    Returns:
        None
    Exceptions:
        InvalidS3PathPattern: when the specified s3 path is invalid pattern
    """

    s3 = S3()
    if path:
        s3.set_bucket_and_path(path)
    else:
        s3.set_s3_bucket()
        s3.set_s3_path()

    fzf = Pyfzf()
    if not local:
        recursive = True if recursive or sync else False
        # don't allow multi_select for recursive operation
        multi_select = True if not recursive else False
        local = fzf.get_local_file(
            search_from_root=root, directory=recursive, hidden=hidden, empty_allow=recursive, multi_select=multi_select)

    if sync:
        sync_s3(exclude=exclude, include=include, from_path=local,
                to_path='s3://%s/%s' % (s3.bucket_name, s3.bucket_path))

    elif recursive:
        upload_list = []
        for root, dirs, files in os.walk(local):
            for filename in files:
                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, local)

                if not exclude_file(exclude, include, relative_path):
                    destination_key = s3.get_s3_destination_key(
                        relative_path, recursive=True)
                    print('(dryrun) upload: %s to s3://%s/%s' %
                          (relative_path, s3.bucket_name, destination_key))
                    upload_list.append(
                        {'local': full_path, 'bucket': s3.bucket_name, 'key': destination_key, 'relative': relative_path})

        if get_confirmation('Confirm?'):
            for item in upload_list:
                print('upload: %s to s3://%s/%s' %
                      (item['relative'], item['bucket'], item['key']))
                transfer = S3Transfer(s3.client)
                transfer.upload_file(item['local'], item['bucket'], item['key'],
                                     callback=S3Progress(item['local']))
                # remove the progress bar
                sys.stdout.write('\033[2K\033[1G')
    else:
        for filepath in local:
            # get the formated s3 destination
            destination_key = s3.get_s3_destination_key(filepath)
            print('(dryrung) upload: %s to s3://%s/%s' %
                  (filepath, s3.bucket_name, destination_key))

        if get_confirmation('Confirm?'):
            for filepath in local:
                destination_key = s3.get_s3_destination_key(filepath)
                print('upload: %s to s3://%s/%s' %
                      (filepath, s3.bucket_name, destination_key))
                transfer = S3Transfer(s3.client)
                transfer.upload_file(filepath, s3.bucket_name, destination_key,
                                     callback=S3Progress(filepath))
                # remove the progress bar
                sys.stdout.write('\033[2K\033[1G')
