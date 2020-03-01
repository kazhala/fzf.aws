# awscform create stack operation
import boto3
from faws_py.util import is_yaml
from faws_py.awscform.helper.tags import get_tags
from faws_py.fzf_py import fzf_py
from faws_py.awscform.helper.process_template import process_yaml_file, process_stack_params
from faws_py.awscform.helper.s3_operations import get_s3_bucket, get_s3_file, get_file_data, get_s3_url

# initialize the cloudformation boto3 client
cloudformation = boto3.client('cloudformation')


def create_stack(args):
    print(args)
    # local flag specified
    if args.local:
        local_path = ''
        # local path specified
        if args.path:
            local_path = args.path[0]
        else:
            file_finder_fzf = fzf_py()
            # use find or fd to find local file
            # search from root dir if root flag sepcified
            local_path = file_finder_fzf.get_local_file(args.root)
        if is_yaml(local_path):
            stack_name = input('StackName: ')
            file_data = process_yaml_file(local_path)
            create_parameters = process_stack_params(
                file_data['dictYaml']['Parameters'])
            tags = get_tags()
            response = cloudformation.create_stack(
                StackName=stack_name,
                TemplateBody=file_data['body'],
                Parameters=create_parameters,
                Tags=tags
            )
            print(response)

    # if no local file flag, get from s3
    else:
        selected_bucket = get_s3_bucket()
        # get the s3 file path
        selected_file = get_s3_file(selected_bucket)

        if is_yaml(selected_file):
            stack_name = input('StackName: ')
            # read the s3 file
            file_data = get_file_data(
                selected_bucket, selected_file, 'yaml')
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
            print(response)
