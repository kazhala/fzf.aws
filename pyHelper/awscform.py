import re
from pyHelper.fzf_py import fzf_py


# helper function to find stacks in all the stack list
def search_stack_in_stacks(stack_name, stacks):
    return [stack for stack in stacks if stack['StackName'] == stack_name][0]


# check if it is yaml file
def is_yaml(file_name):
    return re.match(r'^.*\.(yaml|yml)$', file_name)


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
        if 'Type' in parameters[ParameterKey]:
            print(f"Type: {parameters[ParameterKey]['Type']}")
        if 'ConstraintDescription' in parameters[ParameterKey]:
            print(
                f"ConstraintDescription: {parameters[ParameterKey]['ConstraintDescription']}")
        if 'AllowedPattern' in parameters[ParameterKey]:
            print(
                f"AllowedPattern: {parameters[ParameterKey]['AllowedPattern']}")

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
                user_input = choose_value_fzf.execute_fzf()
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
                ParameterValue = input(f'{ParameterKey}: ')
        # seperater
        print(80*'-')
        create_parameters.append(
            {'ParameterKey': ParameterKey, 'ParameterValue': ParameterValue})
    return create_parameters
