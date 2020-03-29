"""get s3 copy argument for preseving all object information

format the argument into a dict in an attempt to preserve all
previouse information including tags, metadata storage_class
and encryption type
"""


def get_copy_args(s3, s3_key, s3_args, extra_args=False, version=None):
    """get copy argument

    Format the argument into a dict that could be passed into
    s3 function through **keywards

    There are three different cases
    1. normal object rename and construct full argument for s3.client.copy()
    2. normal object rename and construct ExtraArgs for s3Transfer.copy()
        which provides progress bar
    3. versioned object rename and construct argument
        versioned object require to use s3.client.get_object() rather than s3.resource.Object()
        so the return type are different, one is object and one is dict, hence, multiple checkes
        in the handler

    Args:
        s3: object, s3 instance of S3 class
        s3_key: string, the current object key on s3
        s3_args: object, args instance of S3Args
        extra_args: bool, is it for extra_args or full args
        version: string, current object version id
    Returns:
        copy_object_args: dict, the key ward argument for s3.client.copy_object
    """
    if not version:
        s3_obj = s3.resource.Object(s3.bucket_name, s3_key)
        s3_acl = s3_obj.Acl()
    else:
        s3_obj = s3.client.get_object(
            Bucket=s3.bucket_name,
            Key=s3_key,
            VersionId=version
        )
        s3_acl = s3.client.get_object_acl(
            Bucket=s3.bucket_name,
            Key=s3_key,
            VersionId=version
        )

    permission_read = []
    permission_acp_read = []
    permission_acp_write = []
    permission_full = []
    for grantee in s3_acl.grants if not version else s3_acl.get('Grants'):
        if grantee.get('Permission') == 'READ':
            if grantee['Grantee'].get('ID'):
                permission_read.append(
                    'id=' + grantee['Grantee']['ID'])
            elif grantee['Grantee'].get('URI'):
                permission_read.append(
                    'uri=' + grantee['Grantee']['URI'])
        elif grantee['Grantee'].get('Permission') == 'FULL_CONTROL':
            if grantee['Grantee'].get('ID'):
                permission_full.append(
                    'id=' + grantee['Grantee']['ID'])
            elif grantee['Grantee'].get('URI'):
                permission_full.append(
                    'uri=' + grantee['Grantee']['URI'])
        elif grantee.get('Permission') == 'WRITE_ACP':
            if grantee['Grantee'].get('ID'):
                permission_acp_write.append(
                    'id=' + grantee['Grantee']['ID'])
            elif grantee['Grantee'].get('URI'):
                permission_acp_write.append(
                    'uri=' + grantee['Grantee']['URI'])
        elif grantee.get('Permission') == 'READ_ACP':
            if grantee['Grantee'].get('ID'):
                permission_acp_read.append(
                    'id=' + grantee['Grantee']['ID'])
            elif grantee['Grantee'].get('URI'):
                permission_acp_read.append(
                    'uri=' + grantee['Grantee']['URI'])

    if not extra_args:
        copy_object_args = {
            "Bucket": s3.bucket_name,
            "Key": s3_key,
            "CopySource": {
                'Bucket': s3.bucket_name,
                'Key': s3_key
            },
        }
    else:
        copy_object_args = {}

    if s3_args.storage_class:
        copy_object_args['StorageClass'] = s3_args.storage_class
    elif not version and s3_obj.storage_class:
        copy_object_args['StorageClass'] = s3_obj.storage_class
    elif version and s3_obj.get('StorageClass'):
        copy_object_args['StorageClass'] = s3_obj.get('StorageClass')

    if s3_args.encryption:
        if s3_args.encryption != 'None':
            copy_object_args['ServerSideEncryption'] = s3_args.encryption
    elif not version and s3_obj.server_side_encryption:
        copy_object_args['ServerSideEncryption'] = s3_obj.server_side_encryption
    elif version and s3_obj.get('ServerSideEncryption'):
        copy_object_args['ServerSideEncryption'] = s3_obj.get(
            'ServerSideEncryption')

    if s3_args.encryption and s3_args.encryption == 'aws:kms':
        copy_object_args['SSEKMSKeyId'] = s3_args.kms_id
    elif not version and s3_obj.server_side_encryption and s3_obj.server_side_encryption == 'aws:kms':
        copy_object_args['SSEKMSKeyId'] = s3_obj.ssekms_key_id
    elif version and s3_obj.get('SSEKMSKeyId'):
        copy_object_args['SSEKMSKeyId'] = s3_obj.get('SSEKMSKeyId')

    if s3_args.tags:
        copy_object_args['TaggingDirective'] = 'REPLACE'
        copy_object_args['Tagging'] = s3_args.tags

    if s3_args.metadata:
        copy_object_args['Metadata'] = s3_args.metadata
        copy_object_args['MetadataDirective'] = 'REPLACE'

    if s3_args.acl:
        copy_object_args['ACL'] = s3_args.acl
    else:
        if s3_args.acl_full:
            copy_object_args['GrantFullControl'] = s3_args.acl_full
        elif permission_full:
            copy_object_args['GrantFullControl'] = ','.join(
                permission_full)

        if s3_args.acl_read:
            copy_object_args['GrantRead'] = s3_args.acl_read
        elif permission_read:
            copy_object_args['GrantRead'] = ','.join(
                permission_read)

        if s3_args.acl_acp_read:
            copy_object_args['GrantReadACP'] = s3_args.acl_acp_read
        elif permission_acp_read:
            copy_object_args['GrantReadACP'] = ','.join(
                permission_acp_read)

        if s3_args.acl_acp_write:
            copy_object_args['GrantWriteACP'] = s3_args.acl_acp_write
        elif permission_acp_write:
            copy_object_args['GrantWriteACP'] = ','.join(
                permission_acp_write)
    return copy_object_args
