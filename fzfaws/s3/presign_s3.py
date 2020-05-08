"""Contains main function for presign url

Generate presigning url for an s3 object
"""
from fzfaws.s3.s3 import S3


def presign_s3(profile=False, bucket=None, version=False, expires_in=3600):
    """get an object from s3 using fzf and generate presign url

    Args:
        profile: string or bool, use a different profile for operation
        bucket: string, s3 path, if specified, skip fzf selection
        version: bool, whether to search for object version and generate url
        expires_in: number, the expiration period of the url
    Returns:
        None
    Output:
        presignUrl: string, the presign url of the object
    Raises:
        InvalidS3PathPattern: when the input path is not a valid s3 form
            bucketname/path or bucketname/
        NoSelectionMade: when fzf selection is empty
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
