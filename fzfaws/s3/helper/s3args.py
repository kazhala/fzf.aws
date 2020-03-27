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

    def set_extra_args(self):
        self.set_storageclass()
        self.set_ACL()
        self.set_encryption()
        self.set_metadata()
        self.set_tags()

    def set_metadata(self):
        """set the meta data for the object"""

        if get_confirmation('Set meta data?'):
            print(
                'Enter meta data for the upload objects, enter without value will skip tagging')
            print(
                'Metadata format should be a URL Query alike string (e.g. Content-Type=hello&Cache-Control=world)')
            metadata = input('Metadata: ')
            if metadata:
                self._extra_args['Metadata'] = {}
                for item in metadata.split('&'):
                    key, value = item.split('=')
                    self._extra_args['Metadata'][key] = value

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
            self._set_canned_ACL()
        elif result == 'Explicit':
            self._set_explicit_ACL()
        else:
            return

    def _set_explicit_ACL(self):
        """set explicit ACL for grantees and permissions

        Get user id/email first than display fzf allow multi_select
        to select permissions
        """
        print('Enter a list of either the Canonical ID, Account email, Predefined Group url to grant permission (Seperate by comma)')
        print('Format: id=XXX,id=XXX,emailAddress=XXX@gmail.com,uri=http://acs.amazonaws.com/groups/global/AllUsers')
        accounts = input('Accounts: ')
        # get what permission to set
        fzf = Pyfzf()
        fzf.append_fzf('GrantFullControl\n')
        fzf.append_fzf('GrantRead\n')
        fzf.append_fzf('GrantReadACP\n')
        fzf.append_fzf('GrantWriteACP\n')
        results = fzf.execute_fzf(
            empty_allow=True, print_col=1, multi_select=True)
        if not results:
            print(
                'No permission is set, default ACL settings of the bucket would be used')
        else:
            for result in results:
                self._extra_args[result] = str(accounts)

    def _set_canned_ACL(self):
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

    @property
    def extra_args(self):
        return self._extra_args

    @property
    def storage_class(self):
        return self._extra_args.get('StorageClass')

    @property
    def tags(self):
        return self._extra_args.get('Tagging')

    @property
    def encryption(self):
        return self._extra_args.get('ServerSideEncryption')

    @property
    def kms_id(self):
        return self._extra_args.get('SSEKMSKeyId')

    @property
    def acl(self):
        return self._extra_args.get('ACL')
