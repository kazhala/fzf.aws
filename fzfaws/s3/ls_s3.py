"""contains main function for s3 ls command

list files purpose
"""
import json
from fzfaws.s3.s3 import S3


def ls_s3(bucket=False, version=False, deletemark=False):
    """list files and display information on the selected file

    List files with version by specifying the -v flag
    Args:
        bucket: bool, display bucket details instead of object details
        version: bool, determine if version should also be displayed
        deletemark: bool, only list file with deletemark associated
    Returns:
        None
    Exceptions:
        InvalidS3PathPattern: when the specified s3 path is invalid pattern
        NoSelectionMade: when the required fzf selection is empty
        SubprocessError: when the local file search got zero result from fzf(no selection in fzf)
    """
    s3 = S3()
    s3.set_s3_bucket()
    if deletemark:
        version = True
    if not bucket:
        s3.set_s3_object(multi_select=True, version=version,
                         deletemark=deletemark)

    if version:
        obj_versions = s3.get_object_version()

    if bucket:
        response = {}
        acls = s3.client.get_bucket_acl(Bucket=s3.bucket_name)
        versions = s3.client.get_bucket_versioning(Bucket=s3.bucket_name)
        region = s3.client.get_bucket_location(Bucket=s3.bucket_name)
        response['Owner'] = acls.get('Owner')
        response['Region'] = region.get('LocationConstraint')
        try:
            encryption = s3.client.get_bucket_encryption(Bucket=s3.bucket_name)
            response['Encryption'] = encryption.get(
                'ServerSideEncryptionConfiguration')
        except:
            response['Encryption'] = None
        try:
            public = s3.client.get_bucket_policy_status(Bucket=s3.bucket_name)
            response['Public'] = public.get('PolicyStatus').get('IsPublic')
            policy = s3.client.get_bucket_policy(Bucket=s3.bucket_name)
            response['Policy'] = policy.get('Policy')
        except:
            pass
        response['Grants'] = acls.get('Grants')
        response['Versioning'] = versions.get('Status')
        response['MFA'] = versions.get('MFADelete')
        try:
            tags = s3.client.get_bucket_tagging(Bucket=s3.bucket_name)
            response['Tags'] = tags.get('TagSet')
        except:
            response['Tags'] = None
        print(80*'-')
        print('s3://%s' % s3.bucket_name)
        print(json.dumps(response, indent=4, default=str))
        exit()

    elif version:
        for obj_version in obj_versions:
            response = s3.client.head_object(
                Bucket=s3.bucket_name,
                Key=obj_version.get('Key'),
                VersionId=obj_version.get('VersionId')
            )
            tags = s3.client.get_object_tagging(
                Bucket=s3.bucket_name,
                Key=obj_version.get('Key'),
                VersionId=obj_version.get('VersionId')
            )
            acls = s3.client.get_object_acl(
                Bucket=s3.bucket_name,
                Key=obj_version.get('Key'),
                VersionId=obj_version.get('VersionId')
            )
            response.pop('ResponseMetadata', None)
            response['Tags'] = tags.get('TagSet')
            response['Owner'] = acls.get('Owner')
            response['Grants'] = acls.get('Grants')
            print(80*'-')
            print('s3://%s/%s versioned %s' % (s3.bucket_name,
                                               obj_version.get('Key'), obj_version.get('VersionId')))
            print(json.dumps(response, indent=4, default=str))

    else:
        for s3_key in s3.path_list:
            response = s3.client.head_object(
                Bucket=s3.bucket_name,
                Key=s3_key,
            )
            tags = s3.client.get_object_tagging(
                Bucket=s3.bucket_name,
                Key=s3_key
            )
            acls = s3.client.get_object_acl(
                Bucket=s3.bucket_name,
                Key=s3_key
            )
            response.pop('ResponseMetadata', None)
            response['Tags'] = tags.get('TagSet')
            response['Owner'] = acls.get('Owner')
            response['Grants'] = acls.get('Grants')
            print(80*'-')
            print('s3://%s/%s' % (s3.bucket_name, s3_key))
            print(json.dumps(response, indent=4, default=str))
