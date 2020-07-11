"""Module contains a helper function to recursivly walk and get all s3 object's within given path."""
import os
import re
from typing import List, Optional, Tuple

from fzfaws.s3.helper.exclude_file import exclude_file
from fzfaws.utils.exceptions import InvalidS3PathPattern


def walk_s3_folder(
    client,
    bucket: str,
    bucket_path: str,
    root: str = "",
    file_list: Optional[List[Tuple[str, str]]] = None,
    exclude: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
    operation: str = "download",
    destination_path: str = "/",
    destination_bucket: str = "",
) -> List[Tuple[str, str]]:
    """Walk s3 folder recursivly in the given path to obtail all objects.

    Reference: https://stackoverflow.com/a/33350380.
    Recursivly call walk_s3_folder to reach the bottom level and append the file path
    to the file_list.

    Process the destination when root is not bucket root.

    Different types of operation doesn't change the actual walk behavior, it only changes
    the information printed.

    :param client: boto3.client('s3')
    :type client: boto3.client
    :param bucket: name of the bucket
    :type bucket: str
    :param bucket_path: the path to download recursive
    :type bucket_path: str
    :param root: current operation root, when calling walk_s3_folder(), set root to bucket_path
    :type root: str
    :param file_list: accumulated list of file to download, pass in empty array when calling walk_s3_folder()
    :type file_list: List[Tuple[str, str]], Optional
    :param exclude: list of glob pattern to exclude
    :type exclude: List[str], optional
    :param include: list of glob pattern to include
    :type include: List[str], optional
    :param operation: current operation type
        Print different information based on operation type
        download/bucket/delete/object
    :type operation: str
    :param destination_path: the destination root path, could be local path or s3 path
    :type destination_path: str, optional
    :param destination_bucket: the destination bucket name for operation='bucket'
    :type destination_bucket: str, optional
    :return: return the list of tuple of file path to download
    :rtype: List[Tuple[str,str]]

    Example return value:
        [(original_key, destination_key)]
    """
    if file_list is None:
        file_list = []
    if exclude is None:
        exclude = []
    if include is None:
        include = []

    paginator = client.get_paginator("list_objects")
    for result in paginator.paginate(Bucket=bucket, Delimiter="/", Prefix=bucket_path):
        if result.get("CommonPrefixes") is not None:
            for subdir in result.get("CommonPrefixes"):
                file_list = walk_s3_folder(
                    client,
                    bucket,
                    subdir.get("Prefix"),
                    root,
                    file_list,
                    exclude,
                    include,
                    operation,
                    destination_path,
                    destination_bucket,
                )
        for file in result.get("Contents", []):
            if file.get("Key").endswith("/") or not file.get("Key"):
                # user created dir in S3 console will appear in the result and is not downloadable
                continue
            if exclude_file(exclude, include, file.get("Key")):
                continue
            if not root:
                dest_pathname = os.path.join(destination_path, file.get("Key"))
            else:
                # strip off the root if the root is not root of the bucket
                # with this, downloading sub folders like bucket/aws
                # will not create a folder called /aws in the target directory
                # rather, it will just download all files in bucket/aws to the target directory
                # nested folders within bucket/aws will still be created in the target directory
                # doing this because aws cli does it, do not want to change the behavior
                pattern = r"(?<=%s)(?P<root>.*)" % root
                strip_root_path_match = re.search(pattern, file.get("Key"))
                if not strip_root_path_match:
                    # raise exception if root was not found within the filepath
                    raise InvalidS3PathPattern(
                        "Encountered invalid root pattern when walking s3 folders"
                    )
                elif strip_root_path_match.group("root").startswith("/"):
                    # raise exceptions if s3path doesn't end with a "/"
                    raise InvalidS3PathPattern(
                        "Encountered invalid s3 path pattern when walking s3 folder"
                    )
                strip_root_path = strip_root_path_match.group("root")
                dest_pathname = os.path.join(destination_path, strip_root_path)
            if operation == "download":
                print(
                    "(dryrun) download: s3://%s/%s to %s"
                    % (bucket, file.get("Key"), dest_pathname)
                )
            elif operation == "bucket":
                print(
                    "(dryrun) copy: s3://%s/%s to s3://%s/%s"
                    % (bucket, file.get("Key"), destination_bucket, dest_pathname)
                )
            elif operation == "delete":
                print("(dryrun) delete: s3://%s/%s" % (bucket, file.get("Key")))
            elif operation == "object":
                print("(dryrun) update: s3://%s/%s" % (bucket, file.get("Key")))
            file_list.append((file.get("Key"), dest_pathname))
    return file_list
