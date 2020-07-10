"""Contains function to list information of s3."""
import json
from typing import Dict, List, Union

from fzfaws.s3.s3 import S3
from fzfaws.utils import Spinner


def ls_s3(
    profile: Union[str, bool] = False,
    bucket: bool = False,
    version: bool = False,
    deletemark: bool = False,
    url: bool = False,
    uri: bool = False,
    name: bool = False,
    arn: bool = False,
    versionid: bool = False,
    bucketpath: str = None,
) -> None:
    """Display information on the selected s3 file or bucket.

    :param profile: use a different profile for this operation
    :type profile: Union[str, bool], optional
    :param bucket: display bucket details instead of object details
    :type bucket: bool, optional
    :param version: determine of object should be choosen based on version
    :type version: bool, optional
    :param deletemark: only list file with deletemark associated
    :type deletemark: bool, optional
    :param url: display url for the selected object/bucket
    :type url: bool, optional
    :param uri: display uri for the selected object/bucket
    :type uri: bool, optional
    :param name: display selected bucket/object name
    :type name: bool, optional
    :param arn: display selected bucket/object arn
    :type arn: bool, optional
    :param versionid: display selected version's versionid
    :type versionid: bool, optional
    :param bucketpath: specify a bucket to operate
    :type bucketpath: str, optional
    """
    s3 = S3(profile)
    s3.set_bucket_and_path(bucketpath)
    if not s3.bucket_name:
        s3.set_s3_bucket()

    if bucket and url:
        response = s3.client.get_bucket_location(Bucket=s3.bucket_name)
        bucket_location = response["LocationConstraint"]
        print("https://s3-%s.amazonaws.com/%s/" % (bucket_location, s3.bucket_name,))
        return
    if bucket and uri:
        print("s3://%s/" % s3.bucket_name)
        return
    if bucket and name:
        print(s3.bucket_name)
        return
    if bucket and arn:
        print("arn:aws:s3:::%s/" % s3.bucket_name)
        return

    if deletemark:
        version = True
    if not bucket and not s3.path_list[0]:
        s3.set_s3_object(multi_select=True, version=version, deletemark=deletemark)

    obj_versions: List[Dict[str, str]] = []
    if version:
        obj_versions = s3.get_object_version()

    if not url and not uri and not name and not versionid and not arn:
        get_detailed_info(s3, bucket, version, obj_versions)
    elif version:
        if url:
            for obj_version in obj_versions:
                print(
                    s3.get_object_url(
                        version=obj_version.get("VersionId", ""),
                        object_key=obj_version.get("Key", ""),
                    )
                )
        if uri:
            for obj_version in obj_versions:
                print("s3://%s/%s" % (s3.bucket_name, obj_version.get("Key", "")))
        if name:
            for obj_version in obj_versions:
                print("%s/%s" % (s3.bucket_name, obj_version.get("Key", "")))
        if versionid:
            for obj_version in obj_versions:
                print(obj_version.get("VersionId"))
        if arn:
            for obj_version in obj_versions:
                print(
                    "arn:aws:s3:::%s/%s" % (s3.bucket_name, obj_version.get("Key", ""))
                )

    else:
        if url:
            for s3_obj in s3.path_list:
                print(s3.get_object_url(object_key=s3_obj))
        if uri:
            for s3_obj in s3.path_list:
                print("s3://%s/%s" % (s3.bucket_name, s3_obj))
        if name:
            for s3_obj in s3.path_list:
                print("%s/%s" % (s3.bucket_name, s3_obj))
        if arn:
            for s3_obj in s3.path_list:
                print("arn:aws:s3:::%s/%s" % (s3.bucket_name, s3_obj))


def get_detailed_info(
    s3: S3, bucket: bool, version: bool, obj_versions: List[Dict[str, str]]
) -> None:
    """Print detailed information about bucket, object or version.

    :param s3: S3 instance
    :type s3: S3
    :param bucket: print detailed information about the bucket
    :type bucket: bool
    :param version: print detailed information about object version
    :type version: bool
    :param obj_version: list of object versions to print details
    :type obj_version: List[Dict[str, str]]
    """
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
