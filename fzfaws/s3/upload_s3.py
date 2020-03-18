"""handles uploading operation of s3

upload local files/directories to s3
"""
import os
import fnmatch
import subprocess
from fzfaws.s3.s3 import S3
from fzfaws.utils.exceptions import InvalidS3PathPattern
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.util import get_confirmation
from fzfaws.s3.helper.sync_s3 import sync_s3


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
            args.root, directory=recursive, hidden=args.hidden, empty_allow=True)

    if args.sync:
        sync_s3(exclude=args.exclude, include=args.include, from_path=local_path,
                to_path='s3://%s/%s' % (s3.bucket_name, s3.bucket_path))

    elif args.recursive:
        upload_list = []
        for root, dirs, files in os.walk(local_path):
            for filename in files:
                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, local_path)

                should_exclude = False
                # validate the relative_path against exclude list
                for pattern in args.exclude:
                    if fnmatch.fnmatch(relative_path, pattern):
                        should_exclude = True
                # validate against include list if it is previouse denied
                if should_exclude:
                    for pattern in args.include:
                        if fnmatch.fnmatch(relative_path, pattern):
                            should_exclude = False

                if not should_exclude:
                    destination_key = s3.get_s3_destination_key(
                        relative_path, recursive=True)
                    print('(dryrun) upload: %s to s3://%s/%s' %
                          (relative_path, s3.bucket_name, destination_key))
                    upload_list.append(
                        {'local': full_path, 'bucket': s3.bucket_name, 'key': destination_key, 'relative': relative_path})

        if get_confirmation('Confirm?'):
            for item in upload_list:
                print('Uploading %s' % item['relative'])
                s3.client.upload_file(
                    item['local'], item['bucket'], item['key'])

    else:
        # get the formated s3 destination
        destination_key = s3.get_s3_destination_key(local_path)
        print('(dryrung) upload: %s to s3://%s/%s' %
              (local_path, s3.bucket_name, destination_key))

        if get_confirmation('Confirm?'):
            print('Uploading %s' % local_path)
            response = s3.client.upload_file(
                local_path, s3.bucket_name, destination_key)
            print('%s uploaded to s3://%s/%s' %
                  (local_path, s3.bucket_name, destination_key))
