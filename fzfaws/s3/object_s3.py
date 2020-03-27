"""object settings and attributes update

update settings on s3 object
"""
from fzfaws.s3.s3 import S3
from fzfaws.s3.helper.s3args import S3Args


def object_s3(bucket=None, recursive=False, version=False, allversion=False, exclude=[], include=[]):
    """update selected object settings

    Args:
        bucket: string, the bucket or bucket path for upload destination
            format: bucketname or bucketname/path/ or bucketname/filename
        recursive: bool, change the settings recursivly
        version: bool, change the settings for versions of object
        allversion: bool, change the settings for all versions of an object
        exclude: list, list of glob pattern to exclude
        include: list, list of glob pattern to include
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
    elif not s3.path_list:
        s3.set_s3_object(version, multi_select=True)
