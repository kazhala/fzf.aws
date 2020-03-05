# update stack operation
import boto3
from pysrc.util import search_dict_in_list, is_yaml, check_is_valid, is_json
from pysrc.cform.helper.tags import get_tags, update_tags
from pysrc.pyfzf import PyFzf
from pysrc.cform.helper.process_template import process_yaml_file, process_stack_params, process_json_file
from pysrc.cform.helper.s3_operations import get_s3_bucket, get_s3_file, get_file_data, get_s3_url

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
            tags = update_tags(tags)
            new_tags = get_tags(update=True)
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
                file_finder_fzf = PyFzf()
                # search from root dir if root flag sepcified
                local_path = file_finder_fzf.get_local_file(args.root)

            # check if file type is valid
            check_is_valid(local_path)
            # read the file
            if is_yaml(local_path):
                file_data = process_yaml_file(local_path)
            elif is_json(local_path):
                file_data = process_json_file(local_path)

            # process params
            if 'Parameters' in file_data['dictBody']:
                updated_parameters = process_stack_params(
                    file_data['dictBody']['Parameters'])
            else:
                updated_parameters = []
            # get tags from user if flag -t
            tags = stack_details['Tags']
            if args.tag:
                tags = update_tags(tags)
                new_tags = get_tags(update=True)
                for new_tag in new_tags:
                    tags.append(new_tag)
            response = cloudformation.update_stack(
                StackName=stack_name,
                TemplateBody=file_data['body'],
                UsePreviousTemplate=False,
                Parameters=updated_parameters,
                Tags=tags
            )

        # if no local file flag, get from s3
        else:
            selected_bucket = get_s3_bucket()
            # get the s3 file path
            selected_file = get_s3_file(selected_bucket)

            # validate file type
            check_is_valid(selected_file)
            # read the s3 file
            if is_yaml(selected_file):
                file_data = get_file_data(
                    selected_bucket, selected_file, 'yaml')
            elif is_json(selected_file):
                file_data = get_file_data(
                    selected_bucket, selected_file, 'json')

            # get params
            if 'Parameters' in file_data:
                updated_parameters = process_stack_params(
                    file_data['dictBody']['Parameters'])
            else:
                updated_parameters = []
            # get tags from user if flag -t
            tags = stack_details['Tags']
            if args.tag:
                tags = update_tags(tags)
                new_tags = get_tags(update=True)
                for new_tag in new_tags:
                    tags.append(new_tag)
            # s3 object url
            template_body_loacation = get_s3_url(
                selected_bucket, selected_file)
            response = cloudformation.update_stack(
                StackName=stack_name,
                TemplateURL=template_body_loacation,
                Parameters=updated_parameters,
                UsePreviousTemplate=False,
                Tags=tags
            )
    print(response)

    if args.wait:
        waiter = cloudformation.get_waiter('stack_update_complete')
        print('--------------------------------------------------------------------------------')
        print("Waiting for stack to finish update...")
        waiter.wait(
            StackName=stack_name,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 120
            }
        )
        print('Stack update complete')
