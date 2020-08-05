"""Module contains the helper class for constructing extra args for s3."""
import json
from typing import Any, Dict, List, Optional

from PyInquirer import prompt

from fzfaws.kms.kms import KMS
from fzfaws.s3 import S3
from fzfaws.utils import (
    Pyfzf,
    get_confirmation,
    prompt_style,
    URLQueryStringValidator,
    CommaListValidator,
)


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
        choices: List[Dict[str, str]] = []

        if version:
            # only allow modification of the two attributes for versioned object
            # because other modification would introduce a new version
            if not metadata and not acl and not tags:
                choices = [{"name": "ACL"}, {"name": "Tagging"}]
        else:
            if not storage and not acl and not metadata and not encryption and not tags:
                choices = [
                    {"name": "StorageClass"},
                    {"name": "ACL"},
                    {"name": "Encryption"},
                    {"name": "Metadata"},
                    {"name": "Tagging"},
                ]

        questions: List[Dict[str, Any]] = [
            {
                "type": "checkbox",
                "name": "selected_attributes",
                "message": "Select attributes to configure",
                "choices": choices,
            }
        ]
        result = prompt(questions, style=prompt_style)
        if not result:
            raise KeyboardInterrupt

        for attribute in result.get("selected_attributes", []):
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
        questions: List[Dict[str, str]] = [
            {
                "type": "input",
                "name": "metadata",
                "message": "Metadata",
                "validate": URLQueryStringValidator,
                "default": original,
            }
        ]
        print(
            "Metadata format should be a URL Query alike string (e.g. Content-Type=hello&Cache-Control=world)"
        )
        result = prompt(questions, style=prompt_style)
        if not result:
            raise KeyboardInterrupt
        metadata = result.get("metadata", "")
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
        choices = [
            "STANDARD",
            "REDUCED_REDUNDANCY",
            "STANDARD_IA",
            "ONEZONE_IA",
            "INTELLIGENT_TIERING",
            "GLACIER",
            "DEEP_ARCHIVE",
        ]
        questions = [
            {
                "type": "rawlist",
                "name": "selected_class",
                "message": "Select a storage class",
                "choices": choices,
            }
        ]

        if original:
            questions[0]["message"] = "Select a storage class (Original: %s)" % original

        result = prompt(questions, style=prompt_style)

        if not result:
            raise KeyboardInterrupt

        storage_class = result.get("selected_class")

        if storage_class:
            self._extra_args["StorageClass"] = storage_class

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

        choices = [
            "None: use bucket default ACL setting",
            "Canned ACL: select predefined set of grantees and permissions",
            "Explicit ACL: explicitly define grantees and permissions",
        ]

        questions = [
            {
                "type": "rawlist",
                "name": "selected_acl",
                "message": "Select a type of ACL to grant, aws accept either canned ACL or explicit ACL",
                "choices": choices,
                "filter": lambda x: x.split(" ")[0],
            }
        ]
        answers = prompt(questions, style=prompt_style)
        if not answers:
            raise KeyboardInterrupt

        result = answers.get("selected_acl", "None")

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

                print("Current ACL:")
                print(json.dumps(original_acl, indent=4, default=str))
                print("Note: fzfaws cannot preserve previous ACL permission")
                if not get_confirmation("Continue?"):
                    return

        choices = [
            {"name": "GrantFullControl"},
            {"name": "GrantRead"},
            {"name": "GrantReadACP"},
            {"name": "GrantWriteACP"},
        ]
        questions = [
            {
                "type": "checkbox",
                "name": "selected_acl",
                "message": "Select ACL to configure",
                "choices": choices,
            }
        ]
        answers = prompt(questions, style=prompt_style)
        if not answers:
            raise KeyboardInterrupt

        results = answers.get("selected_acl", [])

        if not results:
            print(
                "No permission is set, default ACL settings of the bucket would be used"
            )
        else:
            print(
                "Enter a list of either the Canonical ID, Account email, Predefined Group url to grant permission (seperate by comma)"
            )
            print(
                "Format: id=XXX,id=XXX,emailAddress=XXX@gmail.com,uri=http://acs.amazonaws.com/groups/global/AllUsers"
            )
            for result in results:
                questions = [
                    {
                        "type": "input",
                        "name": "input_acl",
                        "message": result,
                        "validate": CommaListValidator,
                    }
                ]

                if original:
                    if result == "GrantFullControl" and original_acl.get(
                        "FULL_CONTROL"
                    ):
                        questions[0]["default"] = ",".join(
                            original_acl.get("FULL_CONTROL", [])
                        )
                    elif result == "GrantRead" and original_acl.get("READ"):
                        questions[0]["default"] = ",".join(original_acl.get("READ", []))
                    elif result == "GrantReadACP" and original_acl.get("READ_ACP"):
                        questions[0]["default"] = ",".join(
                            original_acl.get("READ_ACP", [])
                        )
                    elif result == "GrantWriteACP" and original_acl.get("WRITE_ACP"):
                        questions[0]["default"] = ",".join(
                            original_acl.get("WRITE_ACP", [])
                        )

                answers = prompt(questions, style=prompt_style)
                if not answers:
                    raise KeyboardInterrupt
                accounts = answers.get("input_acl", "")
                self._extra_args[result] = str(accounts)

    def _set_canned_ACL(self) -> None:
        """Set the canned ACL for the current operation."""
        choices = [
            "private",
            "public-read",
            "public-read-write",
            "authenticated-read",
            "aws-exec-read",
            "bucket-owner-read",
            "bucket-owner-full-control",
        ]
        questions = [
            {
                "type": "rawlist",
                "name": "selected_acl",
                "message": "Select a Canned ACL option",
                "choices": choices,
            }
        ]
        answers = prompt(questions, style=prompt_style)
        if not questions:
            raise KeyboardInterrupt
        result = answers.get("selected_acl")
        if result:
            self._extra_args["ACL"] = result

    def set_encryption(self, original: str = None) -> None:
        """Set the encryption setting.

        :param original: previous value of the encryption
        :type original: str, optional
        """
        choices = [
            "None (Use bucket default setting)",
            "AES256",
            "aws:kms",
        ]
        questions = [
            {
                "type": "rawlist",
                "name": "selected_encryption",
                "message": "select an encryption setting",
                "choices": choices,
            }
        ]
        if original:
            questions[0]["message"] = (
                "select an encryption setting (Original: %s)" % original
            )

        answers = prompt(questions, style=prompt_style)
        if not answers:
            raise KeyboardInterrupt

        result = answers.get("selected_encryption")
        if result:
            self._extra_args["ServerSideEncryption"] = result
        if result == "aws:kms":
            current_region = self.s3.client.get_bucket_location(
                Bucket=self.s3.bucket_name
            )
            current_region = current_region.get("LocationConstraint")
            kms = KMS(self.s3.profile, self.s3.region)
            kms.set_keyids(header="select encryption key to use")
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
            "Tag format should be a URL Query alike string (e.g. tagname=hello&tag2=world)"
        )

        questions = [
            {
                "type": "input",
                "name": "answer",
                "message": "Tags",
                "validate": URLQueryStringValidator,
            }
        ]

        if original:
            original_tags: list = []
            original_values: str = ""
            if not version:
                tags = self.s3.client.get_object_tagging(
                    Bucket=self.s3.bucket_name, Key=self.s3.path_list[0],
                )
                for tag in tags.get("TagSet", []):
                    original_tags.append("%s=%s" % (tag.get("Key"), tag.get("Value")))
                original_values = "&".join(original_tags)
            elif len(version) == 1:
                tags = self.s3.client.get_object_tagging(
                    Bucket=self.s3.bucket_name,
                    Key=self.s3.path_list[0],
                    VersionId=version[0].get("VersionId"),
                )
                for tag in tags.get("TagSet", []):
                    original_tags.append("%s=%s" % (tag.get("Key"), tag.get("Value")))
                original_values = "&".join(original_tags)
            questions[0]["default"] = original_values

        answer = prompt(questions, style=prompt_style)
        if not answer:
            raise KeyboardInterrupt
        tags = answer.get("answer")
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
