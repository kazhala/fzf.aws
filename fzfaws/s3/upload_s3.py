"""handles uploading operation of s3

upload local files/directories to s3
"""
import json
import os
import fnmatch
import subprocess
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
    print(args)

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
    if args.local:
        local_path = args.local[0]
    else:
        recursive = True if args.recursive or args.sync else False
        local_path = fzf.get_local_file(
            args.root, directory=recursive, hidden=args.hidden)

    if args.sync:
        # add in the exclude flag and include flag into the command list
        exclude_list = []
        include_list = []
        for pattern in args.exclude:
            if not exclude_list:
                exclude_list.append('--exclude')
            exclude_list.append(pattern)
        for pattern in args.include:
            if not include_list:
                include_list.append('--include')
            include_list.append(pattern)

        cmd_list = ['aws', 's3', 'sync', local_path, 's3://%s/%s' %
                    (s3.bucket_name, s3.bucket_path)]
        cmd_list.extend(exclude_list)
        cmd_list.extend(include_list)
        cmd_list.append('--dryrun')

        # use subprocess to call aws cli with s3 sync as boto3 doesn't have sync
        # it's even slower if try reproduce the sync behavior with boto3 implemented here
        sync_dry = subprocess.Popen(cmd_list)
        sync_dry.communicate()
        if get_confirmation('Confirm?'):
            cmd_list.pop()
            sync = subprocess.Popen(cmd_list)
            sync.communicate()
            print('%s synced it s3://%s/%s' %
                  (local_path, s3.bucket_name, s3.bucket_path))

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
            response = s3.client.upload_file(
                local_path, s3.bucket_name, destination_key)
            print('%s uploaded' % local_path)
