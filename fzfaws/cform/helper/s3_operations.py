# functions related to getting information from s3
import boto3
from botocore.exceptions import ClientError
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.cform.helper.process_template import process_yaml_body, process_json_body

s3 = boto3.client('s3')
# using s3 resource to read the object data for dynamic parameter input
s3_resource = boto3.resource('s3')


# list all bucket and select one
def get_s3_bucket():
    response = s3.list_buckets()
    s3_bucket_fzf = Pyfzf()
    # prepare fzf string, require each line a bucket
    for bucket in response['Buckets']:
        s3_bucket_fzf.append_fzf(f"bucket: {bucket['Name']}")
        s3_bucket_fzf.append_fzf('\n')
    selected_bucket = s3_bucket_fzf.execute_fzf()
    return selected_bucket


# list all object inside a bucket
def get_s3_file(bucket):
    # get the s3 object
    response = s3.list_objects(
        Bucket=bucket
    )
    s3_object_fzf = Pyfzf()
    # prepare the fzf input for selecting object
    for s3_object in response['Contents']:
        s3_object_fzf.append_fzf(f"object: {s3_object['Key']}")
        s3_object_fzf.append_fzf('\n')
    selected_file = s3_object_fzf.execute_fzf()
    return selected_file


# convert file to python dict
def get_file_data(bucket, file, file_type):
    # read the file data into body variable and use yaml package to process it
    s3_object = s3_resource.Object(
        bucket, file)
    body = s3_object.get()['Body'].read()
    # conver to string from byte
    body = str(body, 'utf-8')
    if file_type == 'yaml':
        body = process_yaml_body(body)
    elif file_type == 'json':
        body = process_json_body(body)
    return body


# return the correct format of the s3 object url
def get_s3_url(bucket, file):
    # get the bucket region for geting the url of the template
    response = s3.get_bucket_location(Bucket=bucket)
    bucket_location = response['LocationConstraint']
    return f"https://s3-{bucket_location}.amazonaws.com/{bucket}/{file}"
