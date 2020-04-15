"""cloudforation create stack operation

create cloudformation stack through both s3 bucket url or local file upload
"""
import json
from fzfaws.cloudformation.helper.file_validation import is_yaml, is_json, check_is_valid
from fzfaws.cloudformation.helper.tags import get_tags
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.cloudformation.helper.process_file import process_json_file, process_yaml_file
from fzfaws.utils.exceptions import NoNameEntered, InvalidFileType
from fzfaws.cloudformation.cloudformation import Cloudformation
from fzfaws.cloudformation.helper.paramprocessor import ParamProcessor
from fzfaws.s3.s3 import S3
from fzfaws.cloudformation.helper.cloudformationargs import CloudformationArgs


def create_stack(profile=False, region=False, local_path=False, root=False, wait=False, extra=False):
    """handle the creation of the cloudformation stack

    Args:
        profile: string or bool, use a different profile for this operation
        region: string or bool, use a different region for this operation
        local_path: string or bool, set local file path for upload
        root: bool, search local file from root
        wait: bool, pause the function and wait for completion
        extra: bool, configure extra settings of the stack, iam, roleback, notification etc
    Raises:
        NoNameEntered: when the new stack receive empty string as stack name
        NoSelectionMade: when the required fzf selection received zero result
        SubprocessError: when the local file search received zero result
    """

    cloudformation = Cloudformation(profile, region)

    # local flag specified
    if local_path:
        if type(local_path) != str:
            fzf = Pyfzf()
            local_path = fzf.get_local_file(
                search_from_root=root, cloudformation=True)

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
                cloudformation.profile, cloudformation.region, file_data['dictBody']['Parameters'])
            paramprocessor.process_stack_params()
            create_parameters = paramprocessor.processed_params
        else:
            create_parameters = []

        cloudformation_args = {
            'cloudformation_action': cloudformation.client.create_stack,
            'StackName': stack_name,
            'TemplateBody': file_data['body'],
            'Parameters': create_parameters
        }

    # if no local file flag, get from s3
    else:
        s3 = S3(cloudformation.profile, cloudformation.region)
        s3.set_s3_bucket()
        s3.set_s3_object()
        if is_yaml(s3.bucket_path):
            file_type = 'yaml'
        elif is_json(s3.bucket_path):
            file_type = 'json'

        check_is_valid(s3.bucket_path)

        stack_name = input('StackName: ')
        if not stack_name:
            raise NoNameEntered('No stack name entered')

        file_data = s3.get_object_data(file_type)
        if 'Parameters' in file_data:
            paramprocessor = ParamProcessor(
                cloudformation.profile, cloudformation.region, file_data['Parameters'])
            paramprocessor.process_stack_params()
            create_parameters = paramprocessor.processed_params
        else:
            create_parameters = []

        template_body_loacation = s3.get_object_url()
        cloudformation_args = {
            'cloudformation_action': cloudformation.client.create_stack,
            'StackName': stack_name,
            'TemplateURL': template_body_loacation,
            'Parameters': create_parameters
        }

    if extra:
        extra_args = CloudformationArgs(cloudformation)
        extra_args.set_extra_args()
        cloudformation_args.update(extra_args.extra_args)
    response = cloudformation.execute_with_capabilities(
        **cloudformation_args)

    response.pop('ResponseMetadata', None)
    print(json.dumps(response, indent=4, default=str))
    print(80*'-')
    print('Stack creation initiated')

    if wait:
        cloudformation.stack_name = stack_name
        cloudformation.wait('stack_create_complete',
                            'Waiting for stack to be ready..')
        print('Stack created')
