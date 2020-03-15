"""cloudformation update stack operations

perform updates to cloudformation
"""
import json
from fzfaws.utils.util import search_dict_in_list
from fzfaws.cform.helper.file_validation import is_yaml, is_json, check_is_valid
from fzfaws.cform.helper.tags import get_tags, update_tags
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.cform.helper.process_file import process_yaml_file, process_json_file
from fzfaws.cform.helper.s3_operations import get_s3_bucket, get_s3_file, get_file_data, get_s3_url
from fzfaws.cform.cform import Cloudformation
from fzfaws.cform.helper.paramprocessor import ParamProcessor


def update_stack(args):
    """handle the update of cloudformation stacks

    Args:
        args: argparse args
        cloudformation: instance of the Cloudformation class
    Returns:
        If is called from changeset_stack() then it will return a dict based on
        the arguments changeset_stack recieved
        example:
            {'Parameters': value, 'Tags': value, 'TemplateBody': value, 'TemplateURL': value}
    """

    cloudformation = Cloudformation()
    cloudformation.get_stack()

    # check to use current template or replace current template
    if not args.replace:
        print('Enter new parameter values, skip to use original value')
        updated_parameters = []
        if 'Parameters' in cloudformation.stack_details:
            parameters = cloudformation.stack_details['Parameters']

            # take new values
            for parameter in parameters:
                parameter_value = input(
                    f'{parameter["ParameterKey"]}({parameter["ParameterValue"]}): ')
                if parameter_value == '""' or parameter_value == "''":
                    updated_parameters.append({
                        'ParameterKey': parameter['ParameterKey'],
                        'ParameterValue': ''
                    })
                elif not parameter_value:
                    updated_parameters.append({
                        'ParameterKey': parameter['ParameterKey'],
                        'UsePreviousValue': True
                    })
                else:
                    updated_parameters.append({
                        'ParameterKey': parameter['ParameterKey'],
                        'ParameterValue': parameter_value
                    })

        tags = cloudformation.stack_details['Tags']
        if args.tag:
            tags = update_tags(tags)
            new_tags = get_tags(update=True)
            for new_tag in new_tags:
                tags.append(new_tag)

        # return the data if this function is called through changeset_stack
        if args.subparser_name == 'changeset':
            return {'Parameters': updated_parameters, 'Tags': tags}

        response = cloudformation.execute_with_capabilities(
            args=args,
            cloudformation_action=cloudformation.client.update_stack,
            StackName=cloudformation.stack_name,
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
                fzf = Pyfzf()
                local_path = fzf.get_local_file(args.root)

            # double check file type
            check_is_valid(local_path)
            if is_yaml(local_path):
                file_data = process_yaml_file(local_path)
            elif is_json(local_path):
                file_data = process_json_file(local_path)

            # process params
            if 'Parameters' in file_data['dictBody']:
                paramprocessor = ParamProcessor(
                    file_data['dictBody']['Parameters'])
                paramprocessor.process_stack_params()
                updated_parameters = paramprocessor.processed_params()
            else:
                updated_parameters = []

            tags = cloudformation.stack_details['Tags']
            if args.tag:
                tags = update_tags(tags)
                new_tags = get_tags(update=True)
                for new_tag in new_tags:
                    tags.append(new_tag)

            if args.subparser_name == 'changeset':
                return {'Parameters': updated_parameters, 'Tags': tags, 'TemplateBody': file_data['body']}

            response = cloudformation.execute_with_capabilities(
                args=args,
                cloudformation_action=cloudformation.client.update_stack,
                StackName=cloudformation.stack_name,
                TemplateBody=file_data['body'],
                UsePreviousTemplate=False,
                Parameters=updated_parameters,
                Tags=tags,
            )

        # if no local file flag, get from s3
        else:
            selected_bucket = get_s3_bucket()
            selected_file = get_s3_file(selected_bucket)

            # validate file type
            check_is_valid(selected_file)
            if is_yaml(selected_file):
                file_data = get_file_data(
                    selected_bucket, selected_file, 'yaml')
            elif is_json(selected_file):
                file_data = get_file_data(
                    selected_bucket, selected_file, 'json')

            # get params
            if 'Parameters' in file_data:
                paramprocessor = ParamProcessor(file_data['Parameters'])
                paramprocessor.process_stack_params()
                updated_parameters = paramprocessor.processed_params
            else:
                updated_parameters = []

            tags = cloudformation.stack_details['Tags']
            if args.tag:
                tags = update_tags(tags)
                new_tags = get_tags(update=True)
                for new_tag in new_tags:
                    tags.append(new_tag)
            template_body_loacation = get_s3_url(
                selected_bucket, selected_file)

            if args.subparser_name == 'changeset':
                return {'Parameters': updated_parameters, 'Tags': tags, 'TemplateURL': template_body_loacation}

            response = cloudformation.execute_with_capabilities(
                args=args,
                cloudformation_action=cloudformation.client.update_stack,
                StackName=cloudformation.stack_name,
                TemplateURL=template_body_loacation,
                Parameters=updated_parameters,
                UsePreviousTemplate=False,
                Tags=tags,
            )

    response.pop('ResponseMetadata', None)
    print(json.dumps(response, indent=4, default=str))
    print(80*'-')
    print('Stack update initiated')

    if args.wait:
        print('Wating for stack to be updated..')
        cloudformation.wait('stack_update_complete')
        print('Stack update complete')
