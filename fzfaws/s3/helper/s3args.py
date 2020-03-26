"""helper class for constructing extra args for s3

using fzf to construct some of the extra argument for s3 operation
"""
from fzfaws.utils.pyfzf import Pyfzf


class S3ExtraArgument:
    """helper class to construct extra argument

    Attributes:
        s3: s3 instance from the S3 class
        _extra_args: dict, extra argument to use for s3 operation
    """

    def __init__(self, s3):
        self.s3 = s3
        self._extra_args = dict()

    def set_storageclass(self):
        """set valid storage class"""

        print('Select a storage class, esc to use the default storage class')
        fzf = Pyfzf()
        fzf.append_fzf('STANDARD\n')
        fzf.append_fzf('REDUCED_REDUNDANCY\n')
        fzf.append_fzf('STANDARD_IA\n')
        fzf.append_fzf('ONEZONE_IA\n')
        fzf.append_fzf('INTELLIGENT_TIERING\n')
        fzf.append_fzf('GLACIER\n')
        fzf.append_fzf('DEEP_ARCHIVE\n')
        result = fzf.execute_fzf(empty_allow=True, print_col=1)
        if result:
            self._extra_args['StorageClass'] = result

    def set_ACL(self):
        """set the ACL for the current operation"""

        print('Select a ACL option, esc to use the default ACL setting for the bucket')
        fzf = Pyfzf()
        fzf.append_fzf('private\n')
        fzf.append_fzf('public-read\n')
        fzf.append_fzf('public-read-write\n')
        fzf.append_fzf('authenticated-read\n')
        fzf.append_fzf('aws-exec-read\n')
        fzf.append_fzf('bucket-owner-read\n')
        fzf.append_fzf('bucket-owner-full-control\n')
        result = fzf.execute_fzf(empty_allow=True, print_col=1)
        if result:
            self._extra_args['ACL'] = result

    def set_encryption(self):
        """set the encryption setting"""
        print('Select a ecryption setting, esc to use the default encryption setting for the bucket')
        fzf = Pyfzf()
        fzf.append_fzf('AES256\n')
        fzf.append_fzf('aws:kms\n')
        result = fzf.execute_fzf(empty_allow=True, print_col=1)
        if result:
            self._extra_args['ServerSideEncryption'] = result
        if result == 'aws:kms':
            current_region = self.s3.client.get_bucket_location(
                Bucket=self.s3.bucket_name)
            print(current_region)

    def get_extra_args(self):
        return self._extra_args
