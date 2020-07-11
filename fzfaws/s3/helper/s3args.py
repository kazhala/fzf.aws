"""Module contains the helper class for constructing extra args for s3."""
import json
from typing import Any, Dict, List, Optional

from fzfaws.kms.kms import KMS
from fzfaws.s3 import S3
from fzfaws.utils import Pyfzf, get_confirmation


class S3Args:
    """A helper class to construct extra argument for extra settings for s3.

    :param s3: a instance from the S3 class
    :type s3: S3
    """

    def __init__(self, s3: S3):
        """Construct the instance."""
        self.s3: S3 = s3
        self._extra_args = {}

    def set_extra_args(
        self,
        storage: bool = False,
        acl: bool = False,
        metadata: bool = False,
        encryption: bool = False,
        tags: bool = False,
        version: Optional[List[Dict[str, str]]] = None,
        upload: bool = False,
    ) -> None:
        """Determine what are the extra settings to set.

        Use fzf menu to let user select attributes to configure.

        :param storage: set storage class
        :type storage: bool, optional
        :param bool: set acl of object
        :type bool: bool, optional
        :param metadata: set metadata
        :type metadata: bool, optional
        :param encryption: set encryption
        :type encryption: bool, optional
        :param tags: set tags
        :type tags: bool, optional
        :param version: specify version of object to modify
        :type version: List[Dict[str, str]], optional
        :param upload: determine if the fzf menu could have empty selection
            allow empty selection during upload operation but not for other operations
        :type upload: bool, optional
        """
        if not version:
            version = []
        attributes: List[str] = []

        if version:
            # only allow modification of the two attributes for versioned object
            # because other modification would introduce a new version
            if not metadata and not acl and not tags:
                fzf = Pyfzf()
                fzf.append_fzf("ACL\n")
                fzf.append_fzf("Tagging")
                attributes = list(
                    fzf.execute_fzf(
                        print_col=1,
                        multi_select=True,
                        empty_allow=False,
                        header="Select attributes to configure",
                    )
                )
        else:
            if not storage and not acl and not metadata and not encryption and not tags:
                fzf = Pyfzf()
                fzf.append_fzf("StorageClass\n")
                fzf.append_fzf("ACL\n")
                fzf.append_fzf("Encryption\n")
                fzf.append_fzf("Metadata\n")
                fzf.append_fzf("Tagging\n")
                attributes = list(
                    fzf.execute_fzf(
                        print_col=1,
                        multi_select=True,
                        empty_allow=upload,
                        header="Select attributes to configure",
                    )
                )

        for attribute in attributes:
            if attribute == "StorageClass":
                storage = True
            elif attribute == "ACL":
                acl = True
            elif attribute == "Metadata":
                metadata = True
            elif attribute == "Encryption":
                encryption = True
            elif attribute == "Tagging":
                tags = True

        old_storage_class: str = ""
        old_encryption: str = ""
        old_metadata: str = ""

        # only show previous values if one object is selected
        if (
            not upload
            and not version
            and len(self.s3.path_list) == 1
            and not self.s3.path_list[0].endswith("/")
            and self.s3.path_list[0] != ""
        ):
            s3_obj = self.s3.resource.Object(self.s3.bucket_name, self.s3.path_list[0])
            old_storage_class = (
                s3_obj.storage_class if s3_obj.storage_class else "STANDARD"
            )
            old_encryption = (
                s3_obj.server_side_encryption
                if s3_obj.server_side_encryption
                else "None"
            )
            if s3_obj.metadata:
                old_metadata_list: list = []
                for key, value in s3_obj.metadata.items():
                    old_metadata_list.append("%s=%s" % (key, value))
                old_metadata = "&".join(old_metadata_list)

        if storage:
            self.set_storageclass(original=old_storage_class)
        if acl:
            display_original = (
                True if not upload and len(self.s3.path_list) == 1 else False
            )
            self.set_ACL(original=display_original, version=version)
        if encryption:
            self.set_encryption(original=old_encryption)
        if metadata:
            self.set_metadata(original=old_metadata)
        if tags:
            display_original = (
                True if not upload and len(self.s3.path_list) == 1 else False
            )
            self.set_tags(original=display_original, version=version)

    def set_metadata(self, original: str = None) -> None:
        """Set the meta data for the object.

        :param original: original value of metadata
        :type original: str, optional
        """
        print(
            "Configure metadata for the objects, enter without value will skip metadata"
        )
        print(
            "Metadata format should be a URL Query alike string (e.g. Content-Type=hello&Cache-Control=world)"
        )

        if original:
            print(80 * "-")
            print("Orignal: %s" % original)
        metadata = input("Metadata: ")
        if metadata:
            self._extra_args["Metadata"] = {}
            for item in metadata.split("&"):
                if "=" not in item:
                    # handle case for hello=world&foo=boo&
                    continue
                key, value = item.split("=")
                self._extra_args["Metadata"][key] = value

    def set_storageclass(self, original: str = None) -> None:
        """Set valid storage class.

        :param original: original value of the storage_class
        :type original: str, optional
        """
        header = "Select a storage class, esc to use the default storage class of the bucket setting"
        if original:
            header += "\nOriginal: %s" % original

        fzf = Pyfzf()
        fzf.append_fzf("STANDARD\n")
        fzf.append_fzf("REDUCED_REDUNDANCY\n")
        fzf.append_fzf("STANDARD_IA\n")
        fzf.append_fzf("ONEZONE_IA\n")
        fzf.append_fzf("INTELLIGENT_TIERING\n")
        fzf.append_fzf("GLACIER\n")
        fzf.append_fzf("DEEP_ARCHIVE\n")
        result = fzf.execute_fzf(empty_allow=True, print_col=1, header=header)
        if result:
            self._extra_args["StorageClass"] = result

    def set_ACL(
        self, original: bool = False, version: Optional[List[Dict[str, str]]] = None
    ) -> None:
        """Set the ACL option.

        :param original: display original value
        :type original: bool, optional
        :param version: version object to set acl for version
        :type version: List[Dict[str, str]], optional
        """
        if not version:
            version = []

        fzf = Pyfzf()
        fzf.append_fzf("None (use bucket default ACL setting)\n")
        fzf.append_fzf("Canned ACL (predefined set of grantees and permissions)\n")
        fzf.append_fzf("Explicit ACL (explicit set grantees and permissions)\n")
        result = fzf.execute_fzf(
            empty_allow=True,
            print_col=1,
            header="Select a type of ACL to grant, aws accept one of canned ACL or explicit ACL",
        )
        if result == "Canned":
            self._set_canned_ACL()
        elif result == "Explicit":
            self._set_explicit_ACL(original=original, version=version)
        else:
            return

    def _set_explicit_ACL(
        self, original: bool = False, version: Optional[List[Dict[str, str]]] = None
    ) -> None:
        """Set explicit ACL for grantees and permissions.

        Get user id/email first than display fzf allow multi_select
        to select permissions

        example version: [{"Key", key, "VersionId": versionid}]

        :param original: display original value
        :type original: bool, optional
        :param version: version of the object
        :type version: List[Dict[str, str]], optional
        """
        original_acl: Dict[str, List[str]] = {
            "FULL_CONTROL": [],
            "WRITE_ACP": [],
            "READ": [],
            "READ_ACP": [],
        }

        # get original values
        if original:
            acls = None
            if not version:
                acls = self.s3.client.get_object_acl(
                    Bucket=self.s3.bucket_name, Key=self.s3.path_list[0]
                )
            elif len(version) == 1:
                acls = self.s3.client.get_object_acl(
                    Bucket=self.s3.bucket_name,
                    Key=self.s3.path_list[0],
                    VersionId=version[0].get("VersionId"),
                )
            if acls:
                owner = acls["Owner"]["ID"]
                for grantee in acls.get("Grants", []):
                    if grantee["Grantee"].get("EmailAddress"):
                        original_acl[grantee["Permission"]].append(
                            "%s=%s"
                            % ("emailAddress", grantee["Grantee"].get("EmailAddress"))
                        )
                    elif (
                        grantee["Grantee"].get("ID")
                        and grantee["Grantee"].get("ID") != owner
                    ):
                        original_acl[grantee["Permission"]].append(
                            "%s=%s" % ("id", grantee["Grantee"].get("ID"))
                        )
                    elif grantee["Grantee"].get("URI"):
                        original_acl[grantee["Permission"]].append(
                            "%s=%s" % ("uri", grantee["Grantee"].get("URI"))
                        )

                print("Current ACL")
                print(json.dumps(original_acl, indent=4, default=str))
                print("Note: fzf.aws cannot preserve previous ACL permission")
                if not get_confirmation("Continue?"):
                    return

        # get what permission to set
        fzf = Pyfzf()
        fzf.append_fzf("GrantFullControl\n")
        fzf.append_fzf("GrantRead\n")
        fzf.append_fzf("GrantReadACP\n")
        fzf.append_fzf("GrantWriteACP\n")
        results: List[str] = list(
            fzf.execute_fzf(empty_allow=True, print_col=1, multi_select=True)
        )
        if not results:
            print(
                "No permission is set, default ACL settings of the bucket would be used"
            )
        else:
            for result in results:
                print("Set permisstion for %s" % result)
                print(
                    "Enter a list of either the Canonical ID, Account email, Predefined Group url to grant permission (Seperate by comma)"
                )
                print(
                    "Format: id=XXX,id=XXX,emailAddress=XXX@gmail.com,uri=http://acs.amazonaws.com/groups/global/AllUsers"
                )
                if original:
                    print(80 * "-")
                    if result == "GrantFullControl" and original_acl.get(
                        "FULL_CONTROL"
                    ):
                        print(
                            "Orignal: %s"
                            % ",".join(original_acl.get("FULL_CONTROL", []))
                        )
                    elif result == "GrantRead" and original_acl.get("READ"):
                        print("Orignal: %s" % ",".join(original_acl.get("READ", [])))
                    elif result == "GrantReadACP" and original_acl.get("READ_ACP"):
                        print(
                            "Orignal: %s" % ",".join(original_acl.get("READ_ACP", []))
                        )
                    elif result == "GrantWriteACP" and original_acl.get("WRITE_ACP"):
                        print(
                            "Orignal: %s" % ",".join(original_acl.get("WRITE_ACP", []))
                        )
                accounts = input("Accounts: ")
                print(80 * "-")
                self._extra_args[result] = str(accounts)

    def _set_canned_ACL(self) -> None:
        """Set the canned ACL for the current operation."""
        fzf = Pyfzf()
        fzf.append_fzf("private\n")
        fzf.append_fzf("public-read\n")
        fzf.append_fzf("public-read-write\n")
        fzf.append_fzf("authenticated-read\n")
        fzf.append_fzf("aws-exec-read\n")
        fzf.append_fzf("bucket-owner-read\n")
        fzf.append_fzf("bucket-owner-full-control\n")
        result: str = str(
            fzf.execute_fzf(
                empty_allow=True,
                print_col=1,
                header="Select a Canned ACL option, esc to use the default ACL setting for the bucket",
            )
        )
        if result:
            self._extra_args["ACL"] = result

    def set_encryption(self, original: str = None) -> None:
        """Set the encryption setting.

        :param original: previous value of the encryption
        :type original: str, optional
        """
        header = "Select a ecryption setting, esc to use the default encryption setting for the bucket"
        if original:
            header += "\nOriginal: %s" % original

        fzf = Pyfzf()
        fzf.append_fzf("None (Use bucket default setting)\n")
        fzf.append_fzf("AES256\n")
        fzf.append_fzf("aws:kms\n")
        result: str = str(fzf.execute_fzf(empty_allow=True, print_col=1, header=header))
        if result:
            self._extra_args["ServerSideEncryption"] = result
        if result == "aws:kms":
            current_region = self.s3.client.get_bucket_location(
                Bucket=self.s3.bucket_name
            )
            current_region = current_region.get("LocationConstraint")
            kms = KMS(self.s3.profile, self.s3.region)
            kms.set_keyids(header="Select encryption key to use")
            self._extra_args["SSEKMSKeyId"] = kms.keyids[0]

    def set_tags(
        self, original: bool = False, version: Optional[List[Dict[str, str]]] = None
    ) -> None:
        """Set the tags.

        :param original: whether to fetch orignal tag value
        :type original: bool, optional
        :param version: version information
        :type version: List[Dict[str, str]], optional
        """
        print(
            "Enter tags for the upload objects, enter without value will skip tagging"
        )
        print(
            "Tag format should be a URL Query alike string (e.g. tagname=hello&tag2=world)"
        )

        if original:
            print(80 * "-")
            original_tags: list = []
            original_values: str = ""
            if not version:
                tags = self.s3.client.get_object_tagging(
                    Bucket=self.s3.bucket_name, Key=self.s3.path_list[0],
                )
                for tag in tags.get("TagSet", []):
                    original_tags.append("%s=%s" % (tag.get("Key"), tag.get("Value")))
                original_values = "&".join(original_tags)
                print("Orignal: %s" % original_values)
            elif len(version) == 1:
                tags = self.s3.client.get_object_tagging(
                    Bucket=self.s3.bucket_name,
                    Key=self.s3.path_list[0],
                    VersionId=version[0].get("VersionId"),
                )
                for tag in tags.get("TagSet", []):
                    original_tags.append("%s=%s" % (tag.get("Key"), tag.get("Value")))
                original_values = "&".join(original_tags)
                print("Orignal: %s" % original_values)

        tags = input("Tags: ")
        if tags:
            self._extra_args["Tagging"] = tags

    def check_tag_acl(self) -> Dict[str, Any]:
        """Check if the only attributes to configure is ACL or Tags.

        This check is to avoid creating unnescessary version of the object
        because only updating tag and acl doesn't require a new version
        to be created.

        If any other settings are touched, then boto3 will create a new version
        of the object if versioning is enabled. By using this check, we can
        avoid any unnescessary creation.

        :return: returns Tags and Grants
        :rtype: Dict[str, Any]

        Example return value:
            {
                "Tags": [
                    {"Key": value, "Value": value}
                ],
                "Grants": {
                    'ACL': string,
                    'GrantFullControl': string,
                    'GrantRead': string,
                    'GrantReadACP': string,
                    'GrantWriteACP': string
                }
            }
        """
        result: Dict[str, Any] = {}

        if (
            not self._extra_args.get("StorageClass")
            and not self._extra_args.get("ServerSideEncryption")
            and not self._extra_args.get("Metadata")
        ):
            if self._extra_args.get("Tagging"):
                tags = []
                for tag in self._extra_args.get("Tagging").split("&"):
                    key, value = tag.split("=")
                    tags.append({"Key": key, "Value": value})
                result["Tags"] = tags
            if self._extra_args.get("ACL"):
                if not result.get("Grants"):
                    result["Grants"] = {}
                result["Grants"]["ACL"] = self._extra_args.get("ACL")
            if self._extra_args.get("GrantFullControl"):
                if not result.get("Grants"):
                    result["Grants"] = {}
                result["Grants"]["GrantFullControl"] = self._extra_args.get(
                    "GrantFullControl"
                )
            if self._extra_args.get("GrantRead"):
                if not result.get("Grants"):
                    result["Grants"] = {}
                result["Grants"]["GrantRead"] = self._extra_args.get("GrantRead")
            if self._extra_args.get("GrantReadACP"):
                if not result.get("Grants"):
                    result["Grants"] = {}
                result["Grants"]["GrantReadACP"] = self._extra_args.get("GrantReadACP")
            if self._extra_args.get("GrantWriteACP"):
                if not result.get("Grants"):
                    result["Grants"] = {}
                result["Grants"]["GrantWriteACP"] = self._extra_args.get(
                    "GrantWriteACP"
                )
        return result

    @property
    def extra_args(self):
        """Return _extra_args."""
        return self._extra_args

    @property
    def storage_class(self):
        """Return storage_class."""
        return self._extra_args.get("StorageClass")

    @property
    def tags(self):
        """Return tags."""
        return self._extra_args.get("Tagging", "")

    @property
    def encryption(self):
        """Return encryption settings."""
        return self._extra_args.get("ServerSideEncryption", "")

    @property
    def kms_id(self):
        """Return kms id."""
        return self._extra_args.get("SSEKMSKeyId", "")

    @property
    def acl(self):
        """Return acl settings."""
        return self._extra_args.get("ACL", "")

    @property
    def metadata(self):
        """Return metadata."""
        return self._extra_args.get("Metadata", {})

    @property
    def acl_full(self):
        """Return acl full control settings."""
        return self._extra_args.get("GrantFullControl", "")

    @property
    def acl_read(self):
        """Return acl read permission."""
        return self._extra_args.get("GrantRead", "")

    @property
    def acl_acp_read(self):
        """Return acl read permission permission."""
        return self._extra_args.get("GrantReadACP", "")

    @property
    def acl_acp_write(self):
        """Return acl write permission permission."""
        return self._extra_args.get("GrantWriteACP", "")
