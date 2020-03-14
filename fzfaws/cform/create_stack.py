"""cloudforation create stack operation

create cloudformation stack through both s3 bucket url or local file upload
"""
import boto3
import json
from fzfaws.utils.util import is_yaml, is_json, check_is_valid
from fzfaws.cform.helper.tags import get_tags
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.cform.helper.process_template import process_yaml_file, process_stack_params, process_json_file
from fzfaws.cform.helper.s3_operations import get_s3_bucket, get_s3_file, get_file_data, get_s3_url
from fzfaws.cform.helper.get_capabilities import get_capabilities, cloudformation_with_capabilities

cloudformation = boto3.client('cloudformation')


def create_stack(args):
    """handle the creation of the cloudformation stack

    Args:
        args: argparser args from main.py in cform
    Returns:
        None
    """
    # local flag specified
    if args.local:
        local_path = ''
        # local path specified
        if args.path:
            local_path = args.path[0]
        else:
            fzf = Pyfzf()
            local_path = fzf.get_local_file(args.root)

        # double check file type
        check_is_valid(local_path)
        stack_name = input('StackName: ')
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

        response = cloudformation_with_capabilities(
            args=args,
            cloudformation_action=cloudformation.create_stack,
            StackName=stack_name,
            TemplateBody=file_data['body'],
            Parameters=create_parameters,
            Tags=tags,
        )

    # if no local file flag, get from s3
    else:
        selected_bucket = get_s3_bucket()
        selected_file = get_s3_file(selected_bucket)
        check_is_valid(selected_file)
        stack_name = input('StackName: ')
        # read the s3 file
        if is_yaml(selected_file):
            file_data = get_file_data(
                selected_bucket, selected_file, 'yaml')
        elif is_json(selected_file):
            file_data = get_file_data(selected_bucket, selected_file, 'json')

        create_parameters = process_stack_params(
            file_data['Parameters'])
        tags = get_tags()
        # s3 object url
        template_body_loacation = get_s3_url(
            selected_bucket, selected_file)
        response = cloudformation_with_capabilities(
            args=args,
            cloudformation_action=cloudformation.create_stack,
            StackName=stack_name,
            TemplateURL=template_body_loacation,
            Parameters=create_parameters,
            Tags=tags,
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