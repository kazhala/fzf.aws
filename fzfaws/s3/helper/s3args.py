"""helper class for constructing extra args for s3

using fzf to construct some of the extra argument for s3 operation
"""
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.kms.kms import KMS
from fzfaws.utils.util import get_confirmation


class S3Args:
    """helper class to construct extra argument

    Attributes:
        s3: s3 instance from the S3 class
        _extra_args: dict, extra argument to use for s3 operation
    """

    def __init__(self, s3):
        self.s3 = s3
        self._extra_args = {}
        # self._extra_args = {
        #     'GrantRead': 'emailAddress=jackyruann@gmail.com,id=ad2161263b64c24d13eb62ec5e4f32fa1e1625965b292d4885afb554a4ffb3a1'
        # }

    def set_extra_args(self):
        self.set_storageclass()
        self.set_ACL()
        self.set_encryption()

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
        """set the ACL option for the current operation"""
        print(
            'Select a type of ACL to grant, aws accept one of canned ACL or explicit ACL')
        fzf = Pyfzf()
        fzf.append_fzf('None (use bucket default ACL setting)\n')
        fzf.append_fzf(
            'Canned ACL (predefined set of grantees and permissions)\n')
        fzf.append_fzf(
            'Explicit ACL (explicit set grantees and permissions)\n')
        result = fzf.execute_fzf(empty_allow=True, print_col=1)
        if result == 'Canned':
            self.set_canned_ACL()
        elif result == 'Explicit':
            self.set_explicit_ACL()
        else:
            return

    def set_explicit_ACL(self):
        """set explicit ACL for grantees and permissions

        Get user id/email first than display fzf allow multi_select
        to select permissions
        """
        print('Enter a list of either the Canonical ID, Account email, Predefined Group url to grant permission (Seperate by comma)')
        print('Format: id=XXX,id=XXX,email=XXX@gmail.com,uri=http://acs.amazonaws.com/groups/global/AllUsers')
        accounts = input('Accounts: ')
        print(accounts)

    def set_canned_ACL(self):
        """set the canned ACL for the current operation"""
        print(
            'Select a Canned ACL option, esc to use the default ACL setting for the bucket')
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
        fzf.append_fzf('None\n')
        fzf.append_fzf('AES256\n')
        fzf.append_fzf('aws:kms\n')
        result = fzf.execute_fzf(empty_allow=True, print_col=1)
        if result and result != 'None':
            self._extra_args['ServerSideEncryption'] = result
        if result == 'aws:kms':
            current_region = self.s3.client.get_bucket_location(
                Bucket=self.s3.bucket_name)
            current_region = current_region.get('LocationConstraint')
            kms = KMS()
            kms.set_keyid()
            self._extra_args['SSEKMSKeyId'] = kms.keyid

    def set_tags(self):
        """set tags for the object"""
        if get_confirmation('Tagging for current upload?'):
            print(
                'Enter tags for the upload objects, enter without value will skip tagging')
            print(
                'Tag format should be a URL Query alike string (e.g. tagname=hello&tag2=world)')
            tags = input('Tags: ')
            if tags:
                self._extra_args['Tagging'] = tags

    def get_extra_args(self):
        return self._extra_args
