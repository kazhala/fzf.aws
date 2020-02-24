import re
import boto3
from pyHelper.fzf_py import fzf_py
from botocore.exceptions import ClientError

ec2 = boto3.client('ec2')
aws_specific_param_type = [
    'AWS::EC2::KeyPair::KeyName',
    'AWS::EC2::SecurityGroup::Id'
]


# helper function to find stacks in all the stack list
def search_stack_in_stacks(stack_name, stacks):
    return [stack for stack in stacks if stack['StackName'] == stack_name][0]


# check if it is yaml file
def is_yaml(file_name):
    return re.match(r'^.*\.(yaml|yml)$', file_name)


def get_selected_param_value(type_name):
    try:
        aws_specified_param_fzf = fzf_py()
        selected_aws_value = None
        if type_name == 'AWS::EC2::KeyPair::KeyName':
            response = ec2.describe_key_pairs()
            for key in response['KeyPairs']:
                aws_specified_param_fzf.append_fzf(key['KeyName'])
                aws_specified_param_fzf.append_fzf('\n')
            selected_aws_value = aws_specified_param_fzf.execute_fzf(
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
                if parameter_type in aws_specific_param_type:
                    user_input = get_selected_param_value(parameter_type)
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
                if parameter_type in aws_specific_param_type:
                    ParameterValue = get_selected_param_value(parameter_type)
                else:
                    ParameterValue = input(f'{ParameterKey}: ')
        # seperater
        print(80*'-')
        create_parameters.append(
            {'ParameterKey': ParameterKey, 'ParameterValue': ParameterValue})
    return create_parameters
