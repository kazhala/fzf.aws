"""handles uploading operation of s3

upload local files/directories to s3
"""
import os
import sys
import fnmatch
import subprocess
from s3transfer import S3Transfer
from fzfaws.s3.s3 import S3
from fzfaws.utils.exceptions import InvalidS3PathPattern
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.util import get_confirmation
from fzfaws.s3.helper.sync_s3 import sync_s3
from fzfaws.s3.helper.exclude_file import exclude_file
from fzfaws.s3.helper.s3progress import S3Progress


def upload_s3(args):
    """upload local files/directories to s3

    upload through boto3 s3 client

    Args:
        args: argparse args
    Returns:
        None
    Exceptions:
        InvalidS3PathPattern: when the specified s3 path is invalid pattern
    """

    s3 = S3()
    if args.path:
        s3.set_bucket_and_path(args.path[0])
    else:
        s3.set_s3_bucket()
        s3.set_s3_path()

    fzf = Pyfzf()
    if args.local:
        local_path = args.local[0]
    else:
        recursive = True if args.recursive or args.sync else False
        local_path = fzf.get_local_file(
            args.root, directory=recursive, hidden=args.hidden, empty_allow=recursive)

    if args.sync:
        sync_s3(exclude=args.exclude, include=args.include, from_path=local_path,
                to_path='s3://%s/%s' % (s3.bucket_name, s3.bucket_path))

    elif args.recursive:
        upload_list = []
        for root, dirs, files in os.walk(local_path):
            for filename in files:
                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, local_path)

                if not exclude_file(args.exclude, args.include, relative_path):
                    destination_key = s3.get_s3_destination_key(
                        relative_path, recursive=True)
                    print('(dryrun) upload: %s to s3://%s/%s' %
                          (relative_path, s3.bucket_name, destination_key))
                    upload_list.append(
                        {'local': full_path, 'bucket': s3.bucket_name, 'key': destination_key, 'relative': relative_path})

        if get_confirmation('Confirm?'):
            for item in upload_list:
                s3.client.upload_file(
                    item['local'], item['bucket'], item['key'])
                transfer = S3Transfer(s3.client)
                transfer.upload_file(item['local'], item['bucket'], item['key'],
                                     callback=S3Progress(item['local']))
                # S3Progress will remove previous line, hence print a empty line
                # to preserve previouse info
                print(' ')
            # remove the previouse empty line
            sys.stdout.write("\033[K")
            print('%s uploaded' % local_path)

    else:
        # get the formated s3 destination
        destination_key = s3.get_s3_destination_key(local_path)
        print('(dryrung) upload: %s to s3://%s/%s' %
              (local_path, s3.bucket_name, destination_key))

        if get_confirmation('Confirm?'):
            print('Uploading %s' % local_path)
            transfer = S3Transfer(s3.client)
            transfer.upload_file(local_path, s3.bucket_name, destination_key,
                                 callback=S3Progress(local_path))
            print('\n%s uploaded to s3://%s/%s' %
                  (local_path, s3.bucket_name, destination_key))
