"""s3 client wrapper 

A centralized position to initial boto3.client('s3'), better
management if user decide to change region or use different profile
"""
import boto3
import re
import json
from fzfaws.utils.session import BaseSession
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.cloudformation.helper.process_file import process_yaml_body, process_json_body
from fzfaws.utils.exceptions import InvalidS3PathPattern


class S3(BaseSession):
    """s3 client wrapper class to interact with boto3.client('s3')

    handles operations directly related to boto3

    Attributes:
        client: object, boto3 client
        resource: object, boto3 resource
        bucket_name: string, name of the selected bucket to interact
        bucket_path: string, path of where the operation should happen
            Note: this attribute may not be a valid s3 key, if recusive operation, is only a sub prefix of s3
            To obtain the destination key during recursive operation, call get_s3_destination_key
        path_list: list, list of s3 path, would be set when multi_select of set_s3_object is used
    """

    def __init__(self, profile=None, region=None):
        super().__init__(profile=profile, region=region, service_name='s3')
        self.bucket_name = None
        self.bucket_path = ''
        self.path_list = []

    def set_s3_bucket(self, header=''):
        """list bucket through fzf and let user select a bucket

        Args:
            header: string, optionally display header in fzf
        """
        response = self.client.list_buckets()
        fzf = Pyfzf()
        fzf.process_list(response['Buckets'], 'Name')
        self.bucket_name = fzf.execute_fzf(header=header)

    def set_bucket_and_path(self, bucket=None):
        """method to set both bucket and path

        use this method to skip fzf selection and
        set both bucket and path directly

        Args:
            bucket: string, format(Bucket/ or Bucket/path/ or Bucket/filename)
        Raises:
            InvalidS3PathPattern: when the specified s3 path is invalid pattern
        """
        if not bucket:
            return
        # check user input
        result, match = self._validate_input_path(bucket)
        if result == 'accesspoint':
            self.bucket_name = match[0][0:-1]
            self.bucket_path = match[1]
            if self.bucket_path:
                self.path_list.append(self.bucket_path)
        elif result == 'bucketpath':
            self.bucket_name = bucket.split('/')[0]
            self.bucket_path = '/'.join(bucket.split('/')[1:])
            if self.bucket_path:
                self.path_list.append(self.bucket_path)
        else:
            raise InvalidS3PathPattern(
                'Invalid s3 path pattern, valid pattern(Bucket/ or Bucket/path/ or Bucket/filename)')

    def set_s3_path(self):
        """set 'path' of s3 to upload or download

        s3 folders are not actually folder, found this path listing on
        https://github.com/boto/boto3/issues/134#issuecomment-116766812

        This method would set the 'path' for s3 however the self.bucket_path cannot be used
        as the destination of upload immediately. This only set the path
        without handling different upload sceanario. Please use the
        get_s3_destination_key after set_s3_path to obtain the correct destination key

        Raises:
            TypeError: would raise when there is no more path to iterate
            Would indicate an end to the loop and print out user current
            selected path
        """
        selected_option = self._get_path_option()
        if selected_option == 'input':
            self.bucket_path = input('Input the path(newname or newpath/): ')
        elif selected_option == 'root':
            print('S3 file path is set to root')
        elif selected_option == 'append' or selected_option == 'interactively':
            paginator = self.client.get_paginator('list_objects')
            fzf = Pyfzf()
            try:
                # interactively search down 'folders' in s3
                while True:
                    for result in paginator.paginate(Bucket=self.bucket_name, Prefix=self.bucket_path, Delimiter='/'):
                        for prefix in result.get('CommonPrefixes'):
                            fzf.append_fzf(prefix.get('Prefix'))
                            fzf.append_fzf('\n')
                    selected_path = fzf.execute_fzf(
                        empty_allow=True, print_col=0)
                    if not selected_path:
                        raise
                    self.bucket_path = selected_path
                    # reset fzf string
                    fzf.fzf_string = ''
            except:
                if selected_option == 'append':
                    new_path = input(
                        'Input the new path to append(newname or newpath/): ')
                    self.bucket_path += new_path
                print('S3 file path is set to %s' %
                      (self.bucket_path if self.bucket_path else 'root'))

    def set_s3_object(self, version=False, multi_select=False, deletemark=False):
        """list object within a bucket and let user select a object.

        stores the file path and the filetype into the instance attributes
        using paginator to get all results

        Args:
            version: bool, enable version find
                when this set to true, the object search would search through 'list_object_versions'
                rather than list_objects so that user could still find the object even after
                they deleted the object
            multi_select: bool, enable multi_select
            deletemark: bool, only display object that has deletemark associated with
                Only works with version=True
        """
        try:
            if not version:
                fzf = Pyfzf()
                paginator = self.client.get_paginator('list_objects')
                for result in paginator.paginate(Bucket=self.bucket_name):
                    fzf.process_list(result.get('Contents'), 'Key')
                if multi_select:
                    self.path_list = fzf.execute_fzf(
                        print_col=-1, multi_select=True)
                else:
                    self.bucket_path = fzf.execute_fzf(print_col=-1)
            else:
                fzf = Pyfzf()
                key_list = []
                paginator = self.client.get_paginator('list_object_versions')
                for result in paginator.paginate(Bucket=self.bucket_name):
                    for version in result.get('DeleteMarkers', []):
                        color_string = '\033[31m' + \
                            'Key: %s' % version.get('Key') + \
                            '\033[0m'
                        if color_string not in key_list:
                            key_list.append(color_string)
                    if not deletemark:
                        for version in result.get('Versions', []):
                            color_string = '\033[31m' + \
                                'Key: %s' % version.get('Key') + \
                                '\033[0m'
                            norm_string = 'Key: %s' % version.get('Key')
                            if color_string not in key_list and norm_string not in key_list:
                                key_list.append(norm_string)
                if key_list:
                    for item in key_list:
                        fzf.append_fzf(item + '\n')
                else:
                    raise
                if multi_select:
                    self.path_list = fzf.execute_fzf(
                        print_col=-1, multi_select=True)
                else:
                    self.bucket_path = fzf.execute_fzf(print_col=-1)
        except:
            print('Bucket is empty or no selection was made')
            exit()

    def get_object_version(self, bucket=None, key=None, delete=False, select_all=False, non_current=False):
        """list object versions through fzf

        Args:
            bucket: string, if not set, class instance's bucket_name would be used
            key: string, if not set, class instance's bucket_path would be used
            delete: bool, allow to choose delete marker
            select_all: bool, skip fzf and pull all version into the return list
            non_current: bool, only put non_current versions into the list
        Returns:
            selected_versions: list, list of dict the user selected
                dict: {'Key': s3 key path, 'VersionId': s3 object id}
        """
        bucket = bucket if bucket else self.bucket_name
        key_list = []
        if key:
            key_list.append(key)
        else:
            key_list.extend(self.path_list)
        selected_versions = []
        for key in key_list:
            version_list = []
            paginator = self.client.get_paginator('list_object_versions')
            for result in paginator.paginate(Bucket=bucket, Prefix=key):
                for version in result.get('Versions', []):
                    if (non_current and not version.get('IsLatest')) or not non_current:
                        version_list.append({
                            'VersionId': version.get('VersionId'),
                            'Key': version.get('Key'),
                            'IsLatest': version.get('IsLatest'),
                            'DeleteMarker': False,
                            'LastModified': version.get('LastModified'),
                        })
                if delete:
                    for marker in result.get('DeleteMarkers', []):
                        version_list.append({
                            'VersionId': marker.get('VersionId'),
                            'Key': marker.get('Key'),
                            'IsLatest': marker.get('IsLatest'),
                            'DeleteMarker': True,
                            'LastModified': marker.get('LastModified'),
                        })
            if not select_all:
                fzf = Pyfzf()
                fzf.process_list(version_list, 'VersionId', 'Key', 'IsLatest',
                                 'DeleteMarker', 'LastModified')
                if delete:
                    for result in fzf.execute_fzf(multi_select=True):
                        selected_versions.append(
                            {'Key': key, 'VersionId': result})
                else:
                    selected_versions.append(
                        {'Key': key, 'VersionId': fzf.execute_fzf()})
            else:
                selected_versions.extend(
                    [{'Key': key, 'VersionId': version.get('VersionId')} for version in version_list])
        return selected_versions

    def get_object_data(self, file_type=None):
        """read the s3 object

        read the s3 object file and if is yaml/json file_type, load the file into dict
        currently is only used for cloudformation

        Args:
            file_type: string, yaml/json, if specified, will load the file into dict
        """
        s3_object = self.resource.Object(self.bucket_name, self.bucket_path)
        body = s3_object.get()['Body'].read()
        body = str(body, 'utf-8')
        if file_type == 'yaml':
            body = process_yaml_body(body)
        elif file_type == 'json':
            body = process_json_body(body)
        return body

    def get_object_url(self):
        """return the object url of the current selected object"""
        response = self.client.get_bucket_location(Bucket=self.bucket_name)
        bucket_location = response['LocationConstraint']
        return "https://s3-%s.amazonaws.com/%s/%s" % (bucket_location, self.bucket_name, self.bucket_path)

    def get_s3_destination_key(self, local_path, recursive=False):
        """set the s3 key for upload destination

        check if the current s3 path ends with '/'
        if not, pass, since is already a valid path
        if yes, append the local file name to the s3 path as the key

        if recursive is set, append '/' to last if '/' does not exist

        Args:
            local_path: string, local file path
            recursive: bool, recursive operation
        """
        if recursive:
            if not self.bucket_path:
                return local_path
            elif self.bucket_path[-1] != '/':
                return self.bucket_path + '/' + local_path
            else:
                return self.bucket_path + local_path
        else:
            if not self.bucket_path:
                # if operation is at root level, return the file name
                return local_path.split('/')[-1]
            elif self.bucket_path[-1] == '/':
                # if specified s3 path, append the file name
                key = local_path.split('/')[-1]
                return self.bucket_path + key
            else:
                return self.bucket_path

    def _validate_input_path(self, user_input):
        """validate if the user input path is valid format"""
        accesspoint_pattern = r"^(arn:aws.*:s3:[a-z\-0-9]+:[0-9]{12}:accesspoint[/:][a-zA-Z0-9\-]{1,63}/)(.*)$"
        path_pattern = r"^(?!arn:.*)(.*/)+.*$"
        if re.match(accesspoint_pattern, user_input):
            return ('accesspoint', re.match(accesspoint_pattern, user_input).groups())
        elif re.match(path_pattern, user_input):
            return ('bucketpath', re.match(path_pattern, user_input).groups())
        else:
            return (None, None)

    def _get_path_option(self):
        """pop up fzf for user to select what to do with the path"""
        fzf = Pyfzf()
        fzf.append_fzf('root: operate on the root level of the bucket\n')
        fzf.append_fzf(
            'interactively: interactively select a path through s3\n')
        fzf.append_fzf('input: manully input the path/name\n')
        fzf.append_fzf(
            'append: interactively select a path and then input new path/name to append')
        return fzf.execute_fzf(print_col=1, header='Please select which level of the bucket would you like to operate in').split(':')[0]
