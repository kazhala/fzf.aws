# update stack operation
import boto3
from faws_py.util import search_dict_in_list, is_yaml
from faws_py.awscform.helper.get_tags import get_tags
from faws_py.fzf_py import fzf_py
from faws_py.awscform.helper.process_template import process_yaml_file, process_stack_params
from faws_py.awscform.helper.s3_operations import get_s3_bucket, get_s3_file, get_file_data, get_s3_url

cloudformation = boto3.client('cloudformation')


def update_stack(args, stack_name, stack_details):
    # check to use current template or replace current template
    if not args.replace:
        print('Enter new parameter values, skip to use original value')
        parameters = stack_details['Parameters']
        updated_parameters = []
        for parameter in parameters:
            # take new values
            parameter_value = input(
                f'{parameter["ParameterKey"]}({parameter["ParameterValue"]}): ')
            # push to list
            if not parameter_value:
                updated_parameters.append({
                    'ParameterKey': parameter['ParameterKey'],
                    'UsePreviousValue': True
                })
            else:
                updated_parameters.append({
                    'ParameterKey': parameter['ParameterKey'],
                    'ParameterValue': parameter_value
                })
        # get tags from user if flag -t
        tags = stack_details['Tags']
        if args.tag:
            # update existing tags
            new_tags = []
            print('Skip the value to use previouse value')
            print('Enter delete in both field to remove a tag')
            for tag in tags:
                tag_key = input(f"Key({tag['Key']}): ")
                if not tag_key:
                    tag_key = tag['Key']
                tag_value = input(f"Value({tag['Value']}): ")
                if not tag_value:
                    tag_value = tag['Value']
                if tag_key == 'delete' and tag_value == 'delete':
                    continue
                new_tags.append(
                    {'Key': tag_key, 'Value': tag_value})
            tags = new_tags
        # create new tags
        if args.newtag:
            new_tags = get_tags()
            for new_tag in new_tags:
                tags.append(new_tag)

        # update the stack
        response = cloudformation.update_stack(
            StackName=stack_name,
            UsePreviousTemplate=True,
            Parameters=updated_parameters,
            Tags=tags
        )
    else:
        # replace existing template
        # check if the new template should be from local
        if args.local:
            local_path = ''
            if args.path:
                local_path = args.path[0]
            else:
                file_finder_fzf = fzf_py()
                # use find or fd to find local file
                # search from root dir if root flag sepcified
                local_path = file_finder_fzf.get_local_file(args.root)
        if is_yaml(local_path):
            file_data = process_yaml_file(local_path)
            updated_parameters = process_stack_params(
                file_data['dictYaml']['Parameters'])
            tags = get_tags()
            response = cloudformation.update_stack(
                StackName=stack_name,
                TemplateBody=file_data['body'],
                UsePreviousTemplate=False,
                Parameters=updated_parameters,
                Tags=tags
            )
    print(response)
