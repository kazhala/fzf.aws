import re
import boto3
from fawsf_py.fzf_py import fzf_py
from botocore.exceptions import ClientError

ec2 = boto3.client('ec2')
aws_specific_param = [
    'AWS::EC2::KeyPair::KeyName',
    'AWS::EC2::SecurityGroup::Id'
]

aws_specific_param_list = [
    'List<AWS::EC2::SecurityGroup::Id>'
]


# helper function to find stacks in all the stack list
def search_stack_in_stacks(stack_name, stacks):
    return [stack for stack in stacks if stack['StackName'] == stack_name][0]


# check if it is yaml file
def is_yaml(file_name):
    return re.match(r'^.*\.(yaml|yml)$', file_name)


# helper function to remove a item in list
def remove_selected_value(aws_value, response_list, key_name):
    return_list = response_list
    for item in response_list:
        if item[key_name] == aws_value:
            return_list.remove(item)
    return return_list


# get the tags
def get_stack_tags():
    tag_list = []
    print('Tags help you identify your sub resources')
    print('A "Name" tag is suggested to enter at the very least')
    print('Skip enter value to stop entering for tags')
    while True:
        tag_name = input('TagName: ')
        if not tag_name:
            break
        tag_value = input('TagValue: ')
        if not tag_value:
            break
        tag_list.append({'Key': tag_name, 'Value': tag_value})
    return tag_list


# handler if parameter type is a list type
def get_list_param_value(type_name):
    try:
        # init a fzf object
        aws_list_param_fzf = fzf_py()
        # a list to keep track of the response items
        response_list = []
        # the list to return the selected values
        return_list = []
        if type_name == 'List<AWS::EC2::SecurityGroup::Id>':
            response = ec2.describe_security_groups()
            response_list = response['SecurityGroups']
            # keep getting the value until user stop input or no more in list
            while True:
                for sg in response_list:
                    aws_list_param_fzf.append_fzf(f"GroupId: {sg['GroupId']}")
                    aws_list_param_fzf.append_fzf(4*' ')
                    aws_list_param_fzf.append_fzf(
                        f"GroupName: {sg['GroupName']}")
                    aws_list_param_fzf.append_fzf('\n')
                # execute fzf
                selected_aws_value = aws_list_param_fzf.execute_fzf(
                    empty_allow=True)
                # empty input stop the loop
                if not selected_aws_value:
                    break
                return_list.append(selected_aws_value)
                # remove the selected item from the response_list
                response_list = remove_selected_value(
                    selected_aws_value, response_list, 'GroupId')
                # clear the string
                aws_list_param_fzf.fzf_string = ''
                # exit if no more item
                if len(response_list) == 0:
                    break
        return return_list
    except ClientError as e:
        print(e)


def get_selected_param_value(type_name):
    try:
        aws_specific_param_fzf = fzf_py()
        selected_aws_value = None
        if type_name == 'AWS::EC2::KeyPair::KeyName':
            response = ec2.describe_key_pairs()
            for key in response['KeyPairs']:
                aws_specific_param_fzf.append_fzf(f"KeyName: {key['KeyName']}")
                aws_specific_param_fzf.append_fzf('\n')
        elif type_name == 'List<AWS::EC2::SecurityGroup::Id>':
            response = ec2.describe_security_groups()
            for sg in response['SecurityGroups']:
                aws_specific_param_fzf.append_fzf(f"GroupId: {sg['GroupId']}")
                aws_specific_param_fzf.append_fzf(4*' ')
                aws_specific_param_fzf.append_fzf(
                    f"GroupName: {sg['GroupName']}")
                aws_specific_param_fzf.append_fzf('\n')
        if aws_specific_param_fzf.fzf_string:
            selected_aws_value = aws_specific_param_fzf.execute_fzf(
                empty_allow=True)
        return selected_aws_value
    except ClientError as e:
        print(e)


# process the template file parameters
def process_yaml_params(parameters):
    print('Enter parameters specified in your template below')
    # prepare array
    create_parameters = []
    for ParameterKey in parameters:
        # initialize var
        default_value = ''
        # print some information
        if 'Description' in parameters[ParameterKey]:
            print(
                f"Description: {parameters[ParameterKey]['Description']}")
        if 'ConstraintDescription' in parameters[ParameterKey]:
            print(
                f"ConstraintDescription: {parameters[ParameterKey]['ConstraintDescription']}")
        if 'AllowedPattern' in parameters[ParameterKey]:
            print(
                f"AllowedPattern: {parameters[ParameterKey]['AllowedPattern']}")
        parameter_type = parameters[ParameterKey]['Type']
        print(f"Type: {parameter_type}")
        # check if default value exists
        if 'Default' in parameters[ParameterKey]:
            default_value = parameters[ParameterKey]['Default']
            # check if fzf could be execute to display selection
            if 'AllowedValues' in parameters[ParameterKey]:
                print(
                    f'Choose a value for {ParameterKey}(Default: {default_value}):')
                choose_value_fzf = fzf_py()
                for allowed_value in parameters[ParameterKey]['AllowedValues']:
                    choose_value_fzf.append_fzf(allowed_value)
                    choose_value_fzf.append_fzf('\n')
                user_input = choose_value_fzf.execute_fzf(empty_allow=True)
            else:
                if parameter_type in aws_specific_param:
                    user_input = get_selected_param_value(parameter_type)
                elif parameter_type in aws_specific_param_list:
                    user_input = get_list_param_value(parameter_type)
                else:
                    user_input = input(
                        f'{ParameterKey}(Default: {default_value}): ')
            # check if user_input, add default value
            if not user_input:
                ParameterValue = default_value
            else:
                ParameterValue = user_input

        # no default value
        else:
            # execute fzf if allowed_value array exists
            if 'AllowedValues' in parameters[ParameterKey]:
                print(f'Choose a value for {ParameterKey}:')
                choose_value_fzf = fzf_py()
                for allowed_value in parameters[ParameterKey]['AllowedValues']:
                    choose_value_fzf.append_fzf(allowed_value)
                    choose_value_fzf.append_fzf('\n')
                ParameterValue = choose_value_fzf.execute_fzf()
            else:
                if parameter_type in aws_specific_param:
                    ParameterValue = get_selected_param_value(parameter_type)
                elif parameter_type in aws_specific_param_list:
                    ParameterValue = get_list_param_value(parameter_type)
                else:
                    ParameterValue = input(f'{ParameterKey}: ')
        # seperater
        print(80*'-')
        if type(ParameterValue) is list:
            ParameterValue = ','.join(ParameterValue)
            create_parameters.append(
                {'ParameterKey': ParameterKey, 'ParameterValue': ParameterValue})
        else:
            create_parameters.append(
                {'ParameterKey': ParameterKey, 'ParameterValue': ParameterValue})
    return create_parameters
