# cform create stack operation
import boto3
import json
from pyfaws.util import is_yaml, is_json, check_is_valid
from pyfaws.cform.helper.tags import get_tags
from pyfaws.pyfzf import PyFzf
from pyfaws.cform.helper.process_template import process_yaml_file, process_stack_params, process_json_file
from pyfaws.cform.helper.s3_operations import get_s3_bucket, get_s3_file, get_file_data, get_s3_url

# initialize the cloudformation boto3 client
cloudformation = boto3.client('cloudformation')


def create_stack(args):
    # local flag specified
    if args.local:
        local_path = ''
        # local path specified
        if args.path:
            local_path = args.path[0]
        else:
            file_finder_fzf = PyFzf()
            # use find or fd to find local file
            # search from root dir if root flag sepcified
            local_path = file_finder_fzf.get_local_file(args.root)
        # validate file type
        check_is_valid(local_path)
        stack_name = input('StackName: ')
        # load the file data
        if is_yaml(local_path):
            file_data = process_yaml_file(local_path)
        elif is_json(local_path):
            file_data = process_json_file(local_path)

        # get params
        if 'Parameters' in file_data['dictBody']:
            create_parameters = process_stack_params(
                file_data['dictBody']['Parameters'])
        else:
            create_parameters = []
        tags = get_tags()
        response = cloudformation.create_stack(
            StackName=stack_name,
            TemplateBody=file_data['body'],
            Parameters=create_parameters,
            Tags=tags
        )

    # if no local file flag, get from s3
    else:
        selected_bucket = get_s3_bucket()
        # get the s3 file path
        selected_file = get_s3_file(selected_bucket)
        # if file_type valid
        check_is_valid(selected_file)
        stack_name = input('StackName: ')
        # read the s3 file
        if is_yaml(selected_file):
            file_data = get_file_data(
                selected_bucket, selected_file, 'yaml')
        elif is_json(selected_file):
            file_data = get_file_data(selected_bucket, selected_file, 'json')

        # get params
        create_parameters = process_stack_params(
            file_data['Parameters'])
        tags = get_tags()
        # s3 object url
        template_body_loacation = get_s3_url(
            selected_bucket, selected_file)
        response = cloudformation.create_stack(
            StackName=stack_name,
            TemplateURL=template_body_loacation,
            Parameters=create_parameters,
            Tags=tags
        )
    response.pop('ResponseMetadata', None)
    print(json.dumps(response, indent=4, default=str))
    print(80*'-')
    print('Stack creation initiated')

    if args.wait:
        waiter = cloudformation.get_waiter('stack_create_complete')
        print('--------------------------------------------------------------------------------')
        print("Waiting for stack to be ready...")
        waiter.wait(
            StackName=stack_name,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 120
            }
        )
        print('Stack create complete')
