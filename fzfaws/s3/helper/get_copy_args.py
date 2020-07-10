"""Contains the function to get s3 copy argument for preserving all object information."""
from typing import Any, Dict
from fzfaws.s3 import S3
from fzfaws.s3.helper.s3args import S3Args


def get_copy_args(
    s3: S3, s3_key: str, s3_args: S3Args, extra_args: bool = False, version: str = None
) -> Dict[str, Any]:
    """Get copy argument for s3 operations.

    Format the argument into a dict that could be passed into
    s3 copy object function through **keywards.

    There are two different cases:
    1. normal object
    2. versioned object

    This function is supposed to be used when needing to preserve all previous object
    information such as encryption type, storage_class etc.

    :param s3: S3 class instance
    :type s3: S3
    :param s3_key: the object key in s3
    :type s3_key: str
    :param s3_args: S3Args instance which contains the argument for s3 client
    :type s3_args: S3Args
    :param extra_args: indicating if this operation is constructing extra_args, if yes, the return value
        won't include bucket name and s3 key
    :type extra_args: bool, optional
    :param version: specify object version id
    :type version: str, optional
    :return: copy object argument
    :rtype: dict
    """
    if version:
        s3_obj = s3.client.get_object(
            Bucket=s3.bucket_name, Key=s3_key, VersionId=version
        )
        s3_acl = s3.client.get_object_acl(
            Bucket=s3.bucket_name, Key=s3_key, VersionId=version
        )
    else:
        s3_obj = s3.client.get_object(Bucket=s3.bucket_name, Key=s3_key)
        s3_acl = s3.client.get_object_acl(Bucket=s3.bucket_name, Key=s3_key)

    permission_read = []
    permission_acp_read = []
    permission_acp_write = []
    permission_full = []
    if check_acl_update(s3_args):
        for grantee in s3_acl.get("Grants"):
            if grantee.get("Permission") == "READ":
                if grantee["Grantee"].get("ID"):
                    permission_read.append("id=" + grantee["Grantee"]["ID"])
                elif grantee["Grantee"].get("URI"):
                    permission_read.append("uri=" + grantee["Grantee"]["URI"])
            elif grantee["Grantee"].get("Permission") == "FULL_CONTROL":
                if grantee["Grantee"].get("ID"):
                    permission_full.append("id=" + grantee["Grantee"]["ID"])
                elif grantee["Grantee"].get("URI"):
                    permission_full.append("uri=" + grantee["Grantee"]["URI"])
            elif grantee.get("Permission") == "WRITE_ACP":
                if grantee["Grantee"].get("ID"):
                    permission_acp_write.append("id=" + grantee["Grantee"]["ID"])
                elif grantee["Grantee"].get("URI"):
                    permission_acp_write.append("uri=" + grantee["Grantee"]["URI"])
            elif grantee.get("Permission") == "READ_ACP":
                if grantee["Grantee"].get("ID"):
                    permission_acp_read.append("id=" + grantee["Grantee"]["ID"])
                elif grantee["Grantee"].get("URI"):
                    permission_acp_read.append("uri=" + grantee["Grantee"]["URI"])

    if not extra_args:
        copy_object_args = {
            "Bucket": s3.bucket_name,
            "Key": s3_key,
            "CopySource": {"Bucket": s3.bucket_name, "Key": s3_key},
        }
    else:
        copy_object_args = {}

    if s3_args.storage_class:
        copy_object_args["StorageClass"] = s3_args.storage_class
    elif s3_obj.get("StorageClass"):
        copy_object_args["StorageClass"] = s3_obj.get("StorageClass")

    if s3_args.encryption:
        if s3_args.encryption != "None":
            copy_object_args["ServerSideEncryption"] = s3_args.encryption
    elif s3_obj.get("ServerSideEncryption"):
        copy_object_args["ServerSideEncryption"] = s3_obj.get("ServerSideEncryption")

    if s3_args.encryption and s3_args.encryption == "aws:kms":
        copy_object_args["SSEKMSKeyId"] = s3_args.kms_id
    elif s3_args.encryption and s3_args.encryption != "aws:kms":
        pass
    elif s3_obj.get("SSEKMSKeyId"):
        copy_object_args["SSEKMSKeyId"] = s3_obj.get("SSEKMSKeyId")

    if s3_args.tags:
        copy_object_args["TaggingDirective"] = "REPLACE"
        copy_object_args["Tagging"] = s3_args.tags

    if s3_args.metadata:
        copy_object_args["Metadata"] = s3_args.metadata
        copy_object_args["MetadataDirective"] = "REPLACE"

    if s3_args.acl:
        copy_object_args["ACL"] = s3_args.acl
    else:
        if s3_args.acl_full:
            copy_object_args["GrantFullControl"] = s3_args.acl_full
        elif permission_full:
            copy_object_args["GrantFullControl"] = ",".join(permission_full)

        if s3_args.acl_read:
            copy_object_args["GrantRead"] = s3_args.acl_read
        elif permission_read:
            copy_object_args["GrantRead"] = ",".join(permission_read)

        if s3_args.acl_acp_read:
            copy_object_args["GrantReadACP"] = s3_args.acl_acp_read
        elif permission_acp_read:
            copy_object_args["GrantReadACP"] = ",".join(permission_acp_read)

        if s3_args.acl_acp_write:
            copy_object_args["GrantWriteACP"] = s3_args.acl_acp_write
        elif permission_acp_write:
            copy_object_args["GrantWriteACP"] = ",".join(permission_acp_write)
    return copy_object_args


def check_acl_update(s3_args) -> bool:
    """Check if any acl is updated.

    If updated, don't preserve any other acl to have the same behavior as put_object_acl.

    :param s3_args: S3Args instance
    :type s3_args: S3Args
    :return: boolean value indicating if the previous acl value should be preserved
    :rtype: bool
    """
    return (
        not s3_args.acl_full
        and not s3_args.acl_read
        and not s3_args.acl_acp_write
        and not s3_args.acl_acp_read
    )
