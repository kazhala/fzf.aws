"""Module contains the progress bar class for s3 transfering."""
import os
import sys
import threading
from typing import Optional


class S3Progress(object):
    """The progress bar for s3 transfering.

    Helper class for displaying s3 upload/download/copy percentage.
    Upload: spcify the filename only.
    Download/Copy: require a bucket and client parameter as well as the filename.

    This class should be used within the callback of the S3Transfer class from boto.
    references:
        https://boto3.amazonaws.com/v1/documentation/api/latest/_modules/boto3/s3/transfer.html
        https://stackoverflow.com/a/41855380

    Example:
        transfer = S3Transfer(boto3.client('s3'))
        transfer.upload_file('/tmp/myfile', 'bucket', 'key',
                             callback=S3Progress('/tmp/myfile'))

    :param filename: file name to upload/download/copy
    :type filename: str
    :param bucket: bucket name, specify this during download or copy
    :type bucket: str
    :param client: boto3 s3 client
    :type client: boto3.client
    :param version_id: specify version id if download/copy is a version
    :type version_id: str
    """

    def __init__(
        self, filename: str, bucket: str = None, client=None, version_id: str = None,
    ) -> None:
        """Construct the progress bar instance."""
        self._filename: str = filename
        self._seen_so_far: float = 0
        self._lock = threading.Lock()
        self._size: float = 0
        if bucket and client:
            if not version_id:
                self._size = client.head_object(Bucket=bucket, Key=filename).get(
                    "ContentLength"
                )
            else:
                self._size = client.head_object(
                    Bucket=bucket, Key=filename, VersionId=version_id
                ).get("ContentLength")
        else:
            self._size = float(os.path.getsize(filename))

    def __call__(self, bytes_amount: float) -> None:
        """Create the bar.

        Locking the thread to a single file.
        """
        with self._lock:
            self._seen_so_far += bytes_amount
            if self._size == 0:
                percentage = 100
            else:
                percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)"
                % (
                    self._filename,
                    self.human_readable_size(self._seen_so_far),
                    self.human_readable_size(self._size),
                    percentage,
                )
            )
            sys.stdout.flush()
            # remove the progress bar line
            sys.stdout.write("\033[2K\033[1G")

    def human_readable_size(self, value: float) -> Optional[str]:
        """Convert bytes to some human readable size.

        Copied from awscli, try to provide the same experience.

        Convert an size in bytes into a human readable format.
        """
        HUMANIZE_SUFFIXES = ("KiB", "MiB", "GiB", "TiB", "PiB", "EiB")
        base = 1024
        bytes_int = float(value)

        if bytes_int == 1:
            return "1 Byte"
        elif bytes_int < base:
            return "%d Bytes" % bytes_int

        for i, suffix in enumerate(HUMANIZE_SUFFIXES):
            unit = base ** (i + 2)
            if round((bytes_int / unit) * base) < base:
                return "%.1f %s" % ((base * bytes_int / unit), suffix)
