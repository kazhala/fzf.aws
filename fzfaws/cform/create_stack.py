"""cloudforation create stack operation

create cloudformation stack through both s3 bucket url or local file upload
"""
import json
from fzfaws.cform.helper.file_validation import is_yaml, is_json, check_is_valid
from fzfaws.cform.helper.tags import get_tags
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.cform.helper.process_file import process_json_file, process_yaml_file
from fzfaws.utils.exceptions import NoNameEntered, InvalidFileType
from fzfaws.cform.cform import Cloudformation
from fzfaws.cform.helper.paramprocessor import ParamProcessor
from fzfaws.s3.s3 import S3


def create_stack(args):
    """handle the creation of the cloudformation stack

    Args:
        args: argparser args from main.py in cform
    Returns:
        None
    """

    cloudformation = Cloudformation()

    # local flag specified
    if args.local:
        local_path = ''
        # local path specified
        if args.path:
            local_path = args.path[0]
        else:
            fzf = Pyfzf()
            local_path = fzf.get_local_file(args.root, cloudformation=True)

        # double check file type
        check_is_valid(local_path)
        stack_name = input('StackName: ')
        if is_yaml(local_path):
            file_data = process_yaml_file(local_path)
        elif is_json(local_path):
            file_data = process_json_file(local_path)

        # get params
        if 'Parameters' in file_data['dictBody']:
            paramprocessor = ParamProcessor(
                file_data['dictBody']['Parameters'])
            paramprocessor.process_stack_params()
            create_parameters = paramprocessor.processed_params
        else:
            create_parameters = []
        tags = get_tags()

        response = cloudformation.execute_with_capabilities(
            args=args,
            cloudformation_action=cloudformation.client.create_stack,
            StackName=stack_name,
            TemplateBody=file_data['body'],
            Parameters=create_parameters,
            Tags=tags,
        )

    # if no local file flag, get from s3
    else:
        s3 = S3()
        s3.set_s3_bucket()
        s3.set_s3_object()
        if is_yaml(s3.object):
            file_type = 'yaml'
        elif is_json(s3.object):
            file_type = 'json'

        check_is_valid(s3.object)

        stack_name = input('StackName: ')
        if not stack_name:
            raise NoNameEntered('No name entered')

        file_data = s3.get_object_data(file_type)
        if 'Parameters' in file_data:
            paramprocessor = ParamProcessor(file_data['Parameters'])
            paramprocessor.process_stack_params()
            create_parameters = paramprocessor.processed_params
        tags = get_tags()

        template_body_loacation = s3.get_object_url()
        response = cloudformation.execute_with_capabilities(
            args=args,
            cloudformation_action=cloudformation.client.create_stack,
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
        print("Waiting for stack to be ready...")
        cloudformation.stack_name = stack_name
        cloudformation.wait('stack_create_complete')
        print('Stack create complete')
