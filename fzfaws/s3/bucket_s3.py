"""bucket transfer operation

contains the main function for moving object between buckets
"""
from fzfaws.s3.s3 import S3


def bucket_s3(from_path=None, to_path=None, recursive=False, sync=False, exclude=[], include=[]):
    """transfer file between buckts

    Args:
        from_path: string, from bucket path
        to_path: string, destination bucket path
        recursive: bool, whether to copy entire folder or just file
        sync: bool, use sync operation through subprocess
        exclude: list, list of glob pattern to exclude
        include: list, list of glob pattern to include afer exclude
    Return:
        None
    """

    s3 = S3()
