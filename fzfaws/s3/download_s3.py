"""s3 download operation

Contains the main function to handle the download operation from s3
"""
import fnmatch
import subprocess
from fzfaws.s3.s3 import S3
from fzfaws.utils.exceptions import InvalidS3PathPattern
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.util import get_confirmation


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
        InvalidS3PathPattern: when the specifed s3 path is invalid pattern
    """
    print('download')
