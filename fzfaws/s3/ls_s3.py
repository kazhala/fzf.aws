"""contains main function for s3 ls command

list files purpose
"""
import json
from typing import Dict, List, Union
from fzfaws.s3.s3 import S3
from fzfaws.utils import Spinner


def ls_s3(
    profile: Union[str, bool] = False,
    bucket: bool = False,
    version: bool = False,
    deletemark: bool = False,
) -> None:
    """list files and display information on the selected file

    :param profile: use a different profile for this operation
    :type profile: Union[str, bool], optional
    :param bucket: display bucket details instead of object details
    :type bucket: bool, optional
    :param version: determine of object should be choosen based on version
    :type version: bool, optional
    :param deletemark: only list file with deletemark associated
    :type deletemark: bool, optional
    """

    s3 = S3(profile)
    s3.set_s3_bucket()
    if deletemark:
        version = True
    if not bucket:
        s3.set_s3_object(multi_select=True, version=version, deletemark=deletemark)

    obj_versions: List[Dict[str, str]] = []
    if version:
        obj_versions = s3.get_object_version()

    get_detailed_info(s3, bucket, version, obj_versions)


def get_detailed_info(
    s3: S3, bucket: bool, version: bool, obj_versions: List[Dict[str, str]]
) -> None:
    if bucket:
        response = {}
        with Spinner.spin(message="Fetching bucket information ..."):
            acls = s3.client.get_bucket_acl(Bucket=s3.bucket_name)
            versions = s3.client.get_bucket_versioning(Bucket=s3.bucket_name)
            region = s3.client.get_bucket_location(Bucket=s3.bucket_name)
            response["Owner"] = acls.get("Owner")
            response["Region"] = region.get("LocationConstraint")
            try:
                encryption = s3.client.get_bucket_encryption(Bucket=s3.bucket_name)
                response["Encryption"] = encryption.get(
                    "ServerSideEncryptionConfiguration"
                )
            except:
                response["Encryption"] = None
            try:
                public = s3.client.get_bucket_policy_status(Bucket=s3.bucket_name)
                response["Public"] = public.get("PolicyStatus").get("IsPublic")
                policy = s3.client.get_bucket_policy(Bucket=s3.bucket_name)
                response["Policy"] = policy.get("Policy")
            except:
                pass
            response["Grants"] = acls.get("Grants")
            response["Versioning"] = versions.get("Status")
            response["MFA"] = versions.get("MFADelete")
            try:
                tags = s3.client.get_bucket_tagging(Bucket=s3.bucket_name)
                response["Tags"] = tags.get("TagSet")
            except:
                response["Tags"] = None
        print(80 * "-")
        print("s3://%s" % s3.bucket_name)
        print(json.dumps(response, indent=4, default=str))

    elif version:
        for obj_version in obj_versions:
            with Spinner.spin(message="Fetching object version information ..."):
                response = s3.client.head_object(
                    Bucket=s3.bucket_name,
                    Key=obj_version.get("Key"),
                    VersionId=obj_version.get("VersionId"),
                )
                tags = s3.client.get_object_tagging(
                    Bucket=s3.bucket_name,
                    Key=obj_version.get("Key"),
                    VersionId=obj_version.get("VersionId"),
                )
                acls = s3.client.get_object_acl(
                    Bucket=s3.bucket_name,
                    Key=obj_version.get("Key"),
                    VersionId=obj_version.get("VersionId"),
                )
                response.pop("ResponseMetadata", None)
                response["Tags"] = tags.get("TagSet")
                response["Owner"] = acls.get("Owner")
                response["Grants"] = acls.get("Grants")
            print(80 * "-")
            print(
                "s3://%s/%s versioned %s"
                % (s3.bucket_name, obj_version.get("Key"), obj_version.get("VersionId"))
            )
            print(json.dumps(response, indent=4, default=str))

    else:
        for s3_key in s3.path_list:
            with Spinner.spin(message="Fetching object information ..."):
                response = s3.client.head_object(Bucket=s3.bucket_name, Key=s3_key,)
                tags = s3.client.get_object_tagging(Bucket=s3.bucket_name, Key=s3_key)
                acls = s3.client.get_object_acl(Bucket=s3.bucket_name, Key=s3_key)
                response.pop("ResponseMetadata", None)
                response["Tags"] = tags.get("TagSet")
                response["Owner"] = acls.get("Owner")
                response["Grants"] = acls.get("Grants")
            print(80 * "-")
            print("s3://%s/%s" % (s3.bucket_name, s3_key))
            print(json.dumps(response, indent=4, default=str))
