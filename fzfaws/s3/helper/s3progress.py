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
    """

    def __init__(self, filename, bucket=None, client=None):
        """constructor

        skip the bucket and client param to use it for upload
        otherwise if specified, would be download/copy between buckets
        """
        self._filename = filename
        self._seen_so_far = 0
        self._lock = threading.Lock()
        if bucket and client:
            self._size = client.head_object(
                Bucket=bucket, Key=filename).get('ContentLength')
        else:
            self._size = float(os.path.getsize(filename))

    def __call__(self, bytes_amount):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))
            sys.stdout.flush()
            sys.stdout.write("\033[K")
