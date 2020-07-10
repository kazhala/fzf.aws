"""Contains function to presign url."""
from typing import Union

from fzfaws.s3.s3 import S3


def presign_s3(
    profile: Union[str, bool] = False,
    bucket: str = None,
    version: bool = False,
    expires_in: int = 3600,
) -> None:
    """Get an object from s3 using fzf and generate presign url for getting the s3 object.

    :param profile: use a different profile for this operation
    :type profile: Union[str, bool]
    :param bucket: s3 bucket name, if specified, skip fzf selection
    :type bucket: str, optional
    :param version: whether to search for object version and generate url
    :type version: bool, optional
    :param expires_in: expiration period of the url
    :type expires_in: int, optional
    """
    s3 = S3(profile)
    s3.set_bucket_and_path(bucket)
    if not s3.bucket_name:
        s3.set_s3_bucket()
    if not s3.path_list[0]:
        s3.set_s3_object(version=version, multi_select=True)

    if version:
        obj_versions = s3.get_object_version()
        for obj_version in obj_versions:
            presign_param = {
                "Bucket": s3.bucket_name,
                "Key": obj_version.get("Key"),
                "VersionId": obj_version.get("VersionId"),
            }
            url = s3.client.generate_presigned_url(
                "get_object", Params=presign_param, ExpiresIn=expires_in
            )
            print(80 * "-")
            print("%s:" % obj_version.get("Key"))
            print(url)
    else:
        for s3_key in s3.path_list:
            presign_param = {"Bucket": s3.bucket_name, "Key": s3_key}
            url = s3.client.generate_presigned_url(
                "get_object", Params=presign_param, ExpiresIn=expires_in
            )
            print(80 * "-")
            print("%s:" % s3_key)
            print(url)
