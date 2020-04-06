"""helper class for constructing extra args for s3

using fzf to construct some of the extra argument for s3 operation
"""
import json
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

    def set_extra_args(self, storage=False, acl=False, metadata=False, encryption=False, tags=False, version=[], upload=False):
        """determine what attributes to set

        Use fzf menu to let user select attributes to configure

        Args:
            storage: bool, set storage
            acl: bool, set acl
            metadata: bool, set metadata
            encryption: bool, set server_side_encryption
            tags: bool, set tags
            version: list, list of selected object version obj {'Key': value, 'VersionId': versionid}.
                It's used to determine the menu item and display previous values
            upload: bool, determine if the menu could have empty selection
        Returns:
            None
        Exceptions:
            NoSelectionMade: When uplaod is false and no selection is made
        """
        attributes = []
        if version:
            if not metadata and not acl and not tags:
                fzf = Pyfzf()
                fzf.append_fzf('ACL\n')
                fzf.append_fzf('Tagging')
                attributes = fzf.execute_fzf(
                    print_col=1, multi_select=True, empty_allow=False, header='Select attributes to configure')
        else:
            if not storage and not acl and not metadata and not encryption and not tags:
                fzf = Pyfzf()
                fzf.append_fzf('StorageClass\n')
                fzf.append_fzf('ACL\n')
                fzf.append_fzf('Encryption\n')
                fzf.append_fzf('Metadata\n')
                fzf.append_fzf('Tagging\n')
                attributes = fzf.execute_fzf(
                    print_col=1, multi_select=True, empty_allow=upload, header='Select attributes to configure')

        for attribute in attributes:
            if attribute == 'StorageClass':
                storage = True
            elif attribute == 'ACL':
                acl = True
            elif attribute == 'Metadata':
                metadata = True
            elif attribute == 'Encryption':
                encryption = True
            elif attribute == 'Tagging':
                tags = True

        old_storage_class = ''
        old_encryption = ''
        old_metadata = ''

        # only show previous values if one object is selected
        if not upload and not version and len(self.s3.path_list) == 1:
            s3_obj = self.s3.resource.Object(
                self.s3.bucket_name, self.s3.path_list[0])
            old_storage_class = s3_obj.storage_class if s3_obj.storage_class else 'STANDARD'
            old_encryption = s3_obj.server_side_encryption if s3_obj.server_side_encryption else 'None'
            if s3_obj.metadata:
                old_metadata = []
                for key, value in s3_obj.metadata.items():
                    old_metadata.append('%s=%s' % (key, value))
                old_metadata = '&'.join(old_metadata)

        elif not upload and version:
            pass

        if storage:
            self.set_storageclass(original=old_storage_class)
        if acl:
            display_original = True if not upload and len(
                self.s3.path_list) == 1 else False
            self.set_ACL(original=display_original, version=version)
        if encryption:
            self.set_encryption(original=old_encryption)
        if metadata:
            self.set_metadata(original=old_metadata)
        if tags:
            display_original = True if not upload and len(
                self.s3.path_list) == 1 else False
            self.set_tags(original=display_original, version=version)

    def set_metadata(self, original=None):
        """set the meta data for the object

        Args:
            original: string, previous value of the object
        """

        print(
            'Enter meta data for the upload objects, enter without value will skip tagging')
        print(
            'Metadata format should be a URL Query alike string (e.g. Content-Type=hello&Cache-Control=world)')
        if original:
            print(80*'-')
            print('Orignal: %s' % original)
        metadata = input('Metadata: ')
        if metadata:
            self._extra_args['Metadata'] = {}
            for item in metadata.split('&'):
                key, value = item.split('=')
                self._extra_args['Metadata'][key] = value

    def set_storageclass(self, original=None):
        """set valid storage class

        Args:
            original: string, previous value of the storage_class
        """

        header = 'Select a storage class, esc to use the default storage class of the bucket setting'
        if original:
            header += '\nOriginal: %s' % original
        fzf = Pyfzf()
        fzf.append_fzf('STANDARD\n')
        fzf.append_fzf('REDUCED_REDUNDANCY\n')
        fzf.append_fzf('STANDARD_IA\n')
        fzf.append_fzf('ONEZONE_IA\n')
        fzf.append_fzf('INTELLIGENT_TIERING\n')
        fzf.append_fzf('GLACIER\n')
        fzf.append_fzf('DEEP_ARCHIVE\n')
        result = fzf.execute_fzf(empty_allow=True, print_col=1, header=header)
        if result:
            self._extra_args['StorageClass'] = result

    def set_ACL(self, original=False, version=[]):
        """set the ACL option for the current operation
        Args:
            original: bool, whether to display original values
            version: list, list of version obj {'Key': key, 'VersionId': versionid}
                Used to fetch previous values in _set_explicit_ACL()
        """
        fzf = Pyfzf()
        fzf.append_fzf('None (use bucket default ACL setting)\n')
        fzf.append_fzf(
            'Canned ACL (predefined set of grantees and permissions)\n')
        fzf.append_fzf(
            'Explicit ACL (explicit set grantees and permissions)\n')
        result = fzf.execute_fzf(empty_allow=True, print_col=1,
                                 header='Select a type of ACL to grant, aws accept one of canned ACL or explicit ACL')
        if result == 'Canned':
            self._set_canned_ACL()
        elif result == 'Explicit':
            self._set_explicit_ACL(original=original, version=version)
        else:
            return

    def _set_explicit_ACL(self, original=False, version=[]):
        """set explicit ACL for grantees and permissions

        Get user id/email first than display fzf allow multi_select
        to select permissions

        Args:
            original: bool, whether to display original values
            version: list, list of version obj {'Key': key, 'VersionId': versionid}
                Used to fetch previous values in _set_explicit_ACL()
        """
        # get original values
        if original:
            if not version:
                acls = self.s3.client.get_object_acl(
                    Bucket=self.s3.bucket_name,
                    Key=self.s3.path_list[0]
                )
            elif len(version) == 1:
                acls = self.s3.client.get_object_acl(
                    Bucket=self.s3.bucket_name,
                    Key=self.s3.path_list[0],
                    VersionId=version[0].get('VersionId')
                )
            if acls:
                owner = acls['Owner']['ID']
                origianl_acl = {
                    'FULL_CONTROL': [],
                    'WRITE_ACP': [],
                    'READ': [],
                    'READ_ACP': []
                }
                for grantee in acls.get('Grants', []):
                    if grantee['Grantee'].get('EmailAddress'):
                        origianl_acl[grantee['Permission']].append('%s=%s' % (
                            'emailAddress', grantee['Grantee'].get('EmailAddress')))
                    elif grantee['Grantee'].get('ID') and grantee['Grantee'].get('ID') != owner:
                        origianl_acl[grantee['Permission']].append(
                            '%s=%s' % ('id', grantee['Grantee'].get('ID')))
                    elif grantee['Grantee'].get('URI'):
                        origianl_acl[grantee['Permission']].append(
                            '%s=%s' % ('uri', grantee['Grantee'].get('URI')))

            print('Current ACL')
            print(json.dumps(origianl_acl, indent=4, default=str))
            print('Note: fzf.aws cannot preserve previous ACL permission')
            if not get_confirmation('Continue?'):
                return

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
                print('Set permisstion for %s' % result)
                print(
                    'Enter a list of either the Canonical ID, Account email, Predefined Group url to grant permission (Seperate by comma)')
                print(
                    'Format: id=XXX,id=XXX,emailAddress=XXX@gmail.com,uri=http://acs.amazonaws.com/groups/global/AllUsers')
                if original:
                    print(80*'-')
                    if result == 'GrantFullControl' and origianl_acl.get('FULL_CONTROL'):
                        print('Orignal: %s' % ",".join(
                            origianl_acl.get('FULL_CONTROL')))
                    elif result == 'GrantRead' and origianl_acl.get('READ'):
                        print('Orignal: %s' %
                              ",".join(origianl_acl.get('READ')))
                    elif result == 'GrantReadACP' and origianl_acl.get('READ_ACP'):
                        print('Orignal: %s' % ",".join(
                            origianl_acl.get('READ_ACP')))
                    elif result == 'GrantWriteACP' and origianl_acl.get('WRITE_ACP'):
                        print('Orignal: %s' % ",".join(
                            origianl_acl.get('WRITE_ACP')))
                accounts = input('Accounts: ')
                print(80*'-')
                self._extra_args[result] = str(accounts)

    def _set_canned_ACL(self):
        """set the canned ACL for the current operation"""
        fzf = Pyfzf()
        fzf.append_fzf('private\n')
        fzf.append_fzf('public-read\n')
        fzf.append_fzf('public-read-write\n')
        fzf.append_fzf('authenticated-read\n')
        fzf.append_fzf('aws-exec-read\n')
        fzf.append_fzf('bucket-owner-read\n')
        fzf.append_fzf('bucket-owner-full-control\n')
        result = fzf.execute_fzf(empty_allow=True, print_col=1,
                                 header='Select a Canned ACL option, esc to use the default ACL setting for the bucket')
        if result:
            self._extra_args['ACL'] = result

    def set_encryption(self, original=None):
        """set the encryption setting

        Args:
            original_type: string, previous value of the encryption
        """
        header = 'Select a ecryption setting, esc to use the default encryption setting for the bucket'
        if original:
            header += '\nOriginal: %s' % original
        fzf = Pyfzf()
        fzf.append_fzf('None\n')
        fzf.append_fzf('AES256\n')
        fzf.append_fzf('aws:kms\n')
        result = fzf.execute_fzf(empty_allow=True, print_col=1, header=header)
        if result:
            self._extra_args['ServerSideEncryption'] = result
        if result == 'aws:kms':
            current_region = self.s3.client.get_bucket_location(
                Bucket=self.s3.bucket_name)
            current_region = current_region.get('LocationConstraint')
            kms = KMS()
            kms.set_keyid()
            self._extra_args['SSEKMSKeyId'] = kms.keyid

    def set_tags(self, original=False, version=[]):
        """set tags for the object

        Args:
            original: bool, whether to fetch original values
            version: list, include version
        """
        print(
            'Enter tags for the upload objects, enter without value will skip tagging')
        print(
            'Tag format should be a URL Query alike string (e.g. tagname=hello&tag2=world)')
        if original:
            print(80*'-')
            if not version:
                tags = self.s3.client.get_object_tagging(
                    Bucket=self.s3.bucket_name,
                    Key=self.s3.path_list[0],
                )
                original_tags = []
                for tag in tags.get('TagSet', []):
                    original_tags.append('%s=%s' %
                                         (tag.get('Key'), tag.get('Value')))
                original_tags = '&'.join(original_tags)
                print('Orignal: %s' % original_tags)
            elif len(version) == 1:
                tags = self.s3.client.get_object_tagging(
                    Bucket=self.s3.bucket_name,
                    Key=self.s3.path_list[0],
                    VersionId=version[0].get('VersionId')
                )
                original_tags = []
                for tag in tags.get('TagSet', []):
                    original_tags.append('%s=%s' %
                                         (tag.get('Key'), tag.get('Value')))
                original_tags = '&'.join(original_tags)
                print('Orignal: %s' % original_tags)

        tags = input('Tags: ')
        if tags:
            self._extra_args['Tagging'] = tags

    def check_tag_acl(self):
        """check if the only attributes to configure is ACL or Tags

        Args:
            None
        Returns:
            result: dict, containing two keys, Tags and Grants
            Structure: {
                'Tags': list, list of tags = {'Key': value, 'Value': value}
                'Grants': dict, = {
                    'ACL': string,
                    'GrantFullControl': string,
                    'GrantRead': string,
                    'GrantReadACP': string,
                    'GrantWriteACP': string
                }
            }
        """
        result = {}
        if not self._extra_args.get('StorageClass') and not self._extra_args.get('ServerSideEncryption') and not self._extra_args.get('Metadata'):
            if self._extra_args.get('Tagging'):
                tags = []
                for tag in self._extra_args.get('Tagging').split('&'):
                    key, value = tag.split('=')
                    tags.append({'Key': key, 'Value': value})
                result['Tags'] = tags
            if self._extra_args.get('ACL'):
                if not result.get('Grants'):
                    result['Grants'] = {}
                result['Grants']['ACL'] = self._extra_args.get('ACL')
            if self._extra_args.get('GrantFullControl'):
                if not result.get('Grants'):
                    result['Grants'] = {}
                result['Grants']['GrantFullControl'] = self._extra_args.get(
                    'GrantFullControl')
            if self._extra_args.get('GrantRead'):
                if not result.get('Grants'):
                    result['Grants'] = {}
                result['Grants']['GrantRead'] = self._extra_args.get(
                    'GrantRead')
            if self._extra_args.get('GrantReadACP'):
                if not result.get('Grants'):
                    result['Grants'] = {}
                result['Grants']['GrantReadACP'] = self._extra_args.get(
                    'GrantReadACP')
            if self._extra_args.get('GrantWriteACP'):
                if not result.get('Grants'):
                    result['Grants'] = {}
                result['Grants']['GrantWriteACP'] = self._extra_args.get(
                    'GrantWriteACP')
        return result

    @property
    def extra_args(self):
        return self._extra_args

    @property
    def storage_class(self):
        return self._extra_args.get('StorageClass')

    @property
    def tags(self):
        return self._extra_args.get('Tagging', '')

    @property
    def encryption(self):
        return self._extra_args.get('ServerSideEncryption', '')

    @property
    def kms_id(self):
        return self._extra_args.get('SSEKMSKeyId', '')

    @property
    def acl(self):
        return self._extra_args.get('ACL', '')

    @property
    def metadata(self):
        return self._extra_args.get('Metadata', {})

    @property
    def acl_full(self):
        return self._extra_args.get('GrantFullControl', '')

    @property
    def acl_read(self):
        return self._extra_args.get('GrantRead', '')

    @property
    def acl_acp_read(self):
        return self._extra_args.get('GrantReadACP', '')

    @property
    def acl_acp_write(self):
        return self._extra_args.get('GrantWriteACP', '')
