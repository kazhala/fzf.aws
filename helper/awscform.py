import re

# helper function to find stacks in all the stack list


def search_stack_in_stacks(stack_name, stacks):
    return [stack for stack in stacks if stack['StackName'] == stack_name][0]


def is_yaml(file_name):
    # check if it is yaml file
    return re.match(r'^.*\.(yaml|yml)$', file_name)


def process_yaml_params(parameters):
    print('Enter parameters specified in your template below')
    create_parameters = []
    for ParameterKey in parameters:
        if 'Description' in parameters[ParameterKey]:
            print(
                f"Description: {parameters[ParameterKey]['Description']}")
        if 'Type' in parameters[ParameterKey]:
            print(f"Type: {parameters[ParameterKey]['Type']}")
        if 'ConstraintDescription' in parameters[ParameterKey]:
            print(
                f"ConstraintDescription: {parameters[ParameterKey]['ConstraintDescription']}")
        if 'AllowedPattern' in parameters[ParameterKey]:
            print(
                f"AllowedPattern: {parameters[ParameterKey]['AllowedPattern']}")
        if 'Default' in parameters[ParameterKey]:
            default_value = parameters[ParameterKey]['Default']
            user_input = input(
                f'{ParameterKey}({default_value}): ')
            if not user_input:
                ParameterValue = default_value
        else:
            ParameterValue = input(f'{ParameterKey}: ')
        print(80*'-')
        create_parameters.append(
            {'ParameterKey': ParameterKey, 'ParameterValue': ParameterValue})
    return create_parameters
