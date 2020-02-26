import boto3
from faws_py.util import search_dict_in_list
from faws_py.awscform.helper.get_tags import get_tags

cloudformation = boto3.client('cloudformation')


def update_stack(args, stack_name, stack_details):
    use_current_template = not args.replace
    if use_current_template:
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
        tags = stack_details['Tags']
        if args.tag:
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
        print('Choose a template to upload')
    print(response)
