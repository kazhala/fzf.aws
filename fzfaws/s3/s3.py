"""s3 client wrapper 

A centralized position to initial boto3.client('s3'), better
management if user decide to change region or use different profile
"""
import boto3
import re
from boto3.session import Session
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.cform.helper.process_file import process_yaml_body, process_json_body
from fzfaws.cform.helper.file_validation import is_yaml, is_json


class S3:
    """s3 client wrapper class to interact with boto3.client('s3')

    handles operations directly related to boto3

    Attributes:
        client: boto3 client
        resource: boto3 resource
        bucket_name: name of the selected bucket to interact
        object: path of the object to process
    """

    def __init__(self):
        self.client = boto3.client('s3')
        self.resource = boto3.resource('s3')
        self.bucket_name = None
        self.object = None
        self.file_type = None
        self.bucket_path = ''

    def set_s3_bucket(self):
        """list bucket through fzf and let user select a bucket"""
        response = self.client.list_buckets()
        fzf = Pyfzf()
        self.bucket_name = fzf.process_list(
            response['Buckets'], 'Name', empty_allow=False)

    def set_s3_path(self):
        """set 'path' of s3 to upload or download

        s3 folders are not actually folder, found this path listing on
        https://github.com/boto/boto3/issues/134#issuecomment-116766812
        """
        paginator = self.client.get_paginator('list_objects')
        self.bucket_path = ''
        fzf = Pyfzf()
        try:
            # interactively search down 'folders' in s3
            while True:
                for result in paginator.paginate(Bucket=self.bucket_name, Prefix=self.bucket_path, Delimiter='/'):
                    for prefix in result.get('CommonPrefixes'):
                        fzf.append_fzf(prefix.get('Prefix'))
                        fzf.append_fzf('\n')
                selected_path = fzf.execute_fzf(empty_allow=True, print_col=1)
                if not selected_path:
                    raise
                self.bucket_path = selected_path
                # reset fzf string
                fzf.fzf_string = ''
        except:
            print('S3 file path is set to %s' %
                  (self.bucket_path if self.bucket_path else 'root'))

    def set_s3_object(self):
        """list object within a bucket and let user select a object.

        stores the file path and the filetype into the instance attributes
        """
        response = self.client.list_objects(Bucket=self.bucket_name)
        fzf = Pyfzf()
        self.object = fzf.process_list(
            response['Contents'], 'Key', empty_allow=False)
        if is_yaml(self.object):
            self.file_type = 'yaml'
        elif is_json(self.object):
            self.file_type = 'json'

    def get_object_data(self):
        """read the s3 object

        read the s3 object file and if is yaml/json file_type, load the file into dict
        """
        s3_object = self.resource.Object(self.bucket_name, self.object)
        body = s3_object.get()['Body'].read()
        body = str(body, 'utf-8')
        if self.file_type == 'yaml':
            body = process_yaml_body(body)
        elif self.file_type == 'json':
            body = process_json_body(body)
        return body

    def get_object_url(self):
        """return the object url of the current selected object"""
        response = self.client.get_bucket_location(Bucket=self.bucket_name)
        bucket_location = response['LocationConstraint']
        return "https://s3-%s.amazonaws.com/%s/%s" % (bucket_location, self.bucket_name, self.object)

    def validate_input_path(self, user_input):
        path_pattern = r"^(.*/)+.*$"
        return re.match(path_pattern, user_input)
