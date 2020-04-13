"""s3 operation progress class

helper class to give boto3 progress indicator
"""
import threading
import sys
import os


class S3Progress(object):
    """s3 operation progress class

    helper class for displaying s3 upload/download/copy percentage
    Upload: spcify the filename only
    Download/Copy: require a bucket and client parameter as well as the filename

    This class should be used within the callback of the S3Transfer class from boto
    reference:
        https://boto3.amazonaws.com/v1/documentation/api/latest/_modules/boto3/s3/transfer.html
        https://stackoverflow.com/a/41855380

    Attributes:
        _filename: string, either a s3 key or local file path
        _seen_so_far: number, how much have transfered
        _lock: object, multi thread lock
        _size: number, total size of the fil
    Example:
        transfer = S3Transfer(boto3.client('s3'))
        transfer.upload_file('/tmp/myfile', 'bucket', 'key',
                             callback=S3Progress('/tmp/myfile'))
    """

    def __init__(self, filename, bucket=None, client=None, version_id='null'):
        """constructor

        skip the bucket and client param to use it for upload
        otherwise if specified, would be download/copy between buckets

        Args:
            filename: string, name of the file or s3 key
            bucket: string, name of the bucket
            client: object, boto3 s3 client
            version_id: string, if specified, would reference specific version
                'null' as default because boto3 return unversioned object with version_id null
        """
        self._filename = filename
        self._seen_so_far = 0
        self._lock = threading.Lock()
        if bucket and client:
            if version_id == 'null':
                self._size = client.head_object(
                    Bucket=bucket, Key=filename).get('ContentLength')
            else:
                self._size = client.head_object(
                    Bucket=bucket, Key=filename, VersionId=version_id).get('ContentLength')
        else:
            self._size = float(os.path.getsize(filename))

    def __call__(self, bytes_amount):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            self._seen_so_far += bytes_amount
            if self._size == 0:
                percentage = 100
            else:
                percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self._filename, self.human_readable_size(
                        self._seen_so_far), self.human_readable_size(self._size),
                    percentage))
            sys.stdout.flush()
            # remove the progress bar line
            sys.stdout.write('\033[2K\033[1G')

    def human_readable_size(self, value):
        """copied from awscli, try to provide the same experience

        Convert an size in bytes into a human readable format.
        """
        HUMANIZE_SUFFIXES = ('KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB')
        one_decimal_point = '%.1f'
        base = 1024
        bytes_int = float(value)

        if bytes_int == 1:
            return '1 Byte'
        elif bytes_int < base:
            return '%d Bytes' % bytes_int

        for i, suffix in enumerate(HUMANIZE_SUFFIXES):
            unit = base ** (i+2)
            if round((bytes_int / unit) * base) < base:
                return '%.1f %s' % ((base * bytes_int / unit), suffix)
