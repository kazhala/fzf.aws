"""s3 download operation

Contains the main function to handle the download operation from s3
"""
import fnmatch
import os
import subprocess
from fzfaws.s3.s3 import S3
from fzfaws.utils.exceptions import InvalidS3PathPattern
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.util import get_confirmation
from fzfaws.s3.helper.sync_s3 import sync_s3


def download_s3(path=None, local=None, recursive=False, root=False, sync=False, exclude=[], include=[], hidden=False):
    """download files/'directory' from s3

    handles sync, download file and download recursive
    from a s3 bucket

    Args:
        path: string, path of the s3 bucket if specified
        local: string, local path if specified
        recursive: bool, opeate recursivly
        root: bool, search file from root directory
        sync: bool, use sync operation
        exclude: list, list of pattern to exclude file
        include: list, list of pattern to include file after exclude
        hidden: bool, include hidden directory during search
    Returns:
        None
    Exceptions:
        InvalidS3PathPattern: when the specified s3 path is invalid pattern
    """

    s3 = S3()
    if path:
        s3.set_bucket_and_path(path)
        # if only the bucket is specified
        # still need to process the bucket path
        if not s3.bucket_path:
            if recursive or sync:
                s3.set_s3_path()
            else:
                s3.set_s3_object()
    else:
        s3.set_s3_bucket()
        if recursive or sync:
            s3.set_s3_path()
        else:
            s3.set_s3_object()

    fzf = Pyfzf()
    if local:
        local_path = local
    else:
        local_path = fzf.get_local_file(
            root, directory=True, hidden=hidden, empty_allow=True)

    if sync:
        sync_s3(exclude=exclude, include=include, from_path='s3://%s/%s' %
                (s3.bucket_name, s3.bucket_path), to_path=local_path)
    elif recursive:
        pass
    else:
        # s3 require a local file name, copy the name of the s3 key
        local_path = os.path.join(local_path, s3.bucket_path.split('/')[-1])
        # due the face without recursive flag s3.bucket_path is set by s3.set_s3_object
        # the bucket_path is the valid s3 key so we don't need to call s3.get_s3_destination_key
        print('(dryrung) download: s3://%s/%s to %s' %
              (s3.bucket_name, s3.bucket_path, local_path))
        if get_confirmation('Confirm?'):
            print('Downloading s3://%s/%s' % (s3.bucket_name, s3.bucket_path))
            response = s3.client.download_file(
                s3.bucket_name, s3.bucket_path, local_path)
            print('s3://%s/%s downloaded to %s' %
                  (s3.bucket_name, s3.bucket_path, local_path))
