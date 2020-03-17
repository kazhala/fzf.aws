"""handles uploading operation of s3

upload local files/directories to s3
"""
import json
from fzfaws.s3.s3 import S3
from fzfaws.utils.exceptions import InvalidS3PathPattern
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.util import get_confirmation


def upload_s3(args):
    """upload local files/directories to s3

    upload through boto3 s3 client

    Args:
        args: argparse args
    Returns:
        None
    Exceptions:
        InvalidS3PathPattern: when the -p flag specifed s3 path is invalid pattern
    """

    s3 = S3()
    if args.path:
        try:
            if s3.validate_input_path(args.path[0]):
                s3.bucket_name = args.path[0].split('/')[0]
                s3.bucket_path = '/'.join(args.path[0].split('/')[1:])
            else:
                raise InvalidS3PathPattern
        except InvalidS3PathPattern:
            print(
                'Invalid s3 path pattern, valid pattern(Bucket/ or Bucket/path/to/upload)')
            exit()
    else:
        s3.set_s3_bucket()
        s3.set_s3_path()

    fzf = Pyfzf()
    local_path = fzf.get_local_file(args.root)
    s3.set_s3_key(local_path)
    print('%s will be uploaded to %s/%s' %
          (local_path, s3.bucket_name, s3.bucket_path))
    if get_confirmation('Confirm?'):
        response = s3.client.upload_file(
            local_path, s3.bucket_name, s3.bucket_path)
        print('File uploaded')
