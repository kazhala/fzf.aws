# functions related to processing a new template
import boto3
import yaml
import json
from pysrc.fzf_py import fzf_py
from botocore.exceptions import ClientError
from pysrc.util import remove_dict_from_list, search_dict_in_list, check_dict_value_in_list

# make yaml class ignore all undefined tags and keep parsing
# yaml doesn't understand all the !Ref, !FindInMap etc
yaml.SafeLoader.add_multi_constructor('!', lambda loader, suffix, node: None)


ec2 = boto3.client('ec2')
route53 = boto3.client('route53')

# aws specific params that require making request
aws_specific_param = [
    'AWS::EC2::AvailabilityZone::Name',
    'AWS::EC2::Instance::Id',
    'AWS::EC2::KeyPair::KeyName',
    'AWS::EC2::SecurityGroup::GroupName',
    'AWS::EC2::SecurityGroup::Id',
    'AWS::EC2::Subnet::Id',
    'AWS::EC2::Volume::Id',
    'AWS::EC2::VPC::Id',
    'AWS::Route53::HostedZone::Id'
]

aws_specific_param_list = [
    'List<AWS::EC2::SecurityGroup::Id>'
]


# read yaml file and return the body
def process_yaml_file(path):
    with open(path, 'r') as body:
        # read all data into template_body for boto3 param
        body = body.read()
        # load yaml into pythong dict
        formated_body = yaml.safe_load(body)
        return {'body': body, 'dictBody': formated_body}


# read the json file and return the body
def process_json_file(path):
    with open(path, 'r') as body:
        # read raw body
        body = body.read()
        formated_body = json.loads(body)
        return {'body': body, 'dictBody': formated_body}


# process the yaml body
def process_yaml_body(file_body):
    return yaml.safe_load(file_body)


# process the json body
def process_json_body(file_body):
    return json.loads(file_body)


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
                    aws_list_param_fzf.append_fzf(2*' ')
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
                response_list = remove_dict_from_list(
                    selected_aws_value, response_list, 'GroupId')
                # clear the string
                aws_list_param_fzf.fzf_string = ''
                # exit if no more item
                if len(response_list) == 0:
                    break

        return return_list
    except ClientError as e:
        print(e)


# use fzf to display aws specific parameters
def get_selected_param_value(type_name):
    try:
        # init fzf
        aws_specific_param_fzf = fzf_py()
        selected_aws_value = None
        if type_name == 'AWS::EC2::KeyPair::KeyName':
            response = ec2.describe_key_pairs()
            for key in response['KeyPairs']:
                aws_specific_param_fzf.append_fzf(f"KeyName: {key['KeyName']}")
                aws_specific_param_fzf.append_fzf('\n')

        elif type_name == 'AWS::EC2::SecurityGroup::Id':
            response = ec2.describe_security_groups()
            for sg in response['SecurityGroups']:
                aws_specific_param_fzf.append_fzf(
                    f"GroupId: {sg['GroupId']}")
                aws_specific_param_fzf.append_fzf(2*' ')
                aws_specific_param_fzf.append_fzf(
                    f"GroupName: {sg['GroupName']}")
                aws_specific_param_fzf.append_fzf('\n')

        elif type_name == 'AWS::EC2::AvailabilityZone::Name':
            response = ec2.describe_availability_zones()
            for zone in response['AvailabilityZones']:
                aws_specific_param_fzf.append_fzf(
                    f"AvailabilityZone: {zone['ZoneName']}")
                aws_specific_param_fzf.append_fzf('\n')

        elif type_name == 'AWS::EC2::Instance::Id':
            response = ec2.describe_instances()
            for instance in response['Reservations']:
                aws_specific_param_fzf.append_fzf(
                    f"InstanceId: {instance['Instances'][0]['InstanceId']}")
                aws_specific_param_fzf.append_fzf('\n')

        elif type_name == 'AWS::EC2::SecurityGroup::GroupName':
            response = ec2.describe_security_groups()
            for sg in response['SecurityGroups']:
                aws_specific_param_fzf.append_fzf(
                    f"GroupName: {sg['GroupName']}")
                aws_specific_param_fzf.append_fzf('\n')

        elif type_name == 'AWS::EC2::Subnet::Id':
            response = ec2.describe_subnets()
            for subnet in response['Subnets']:
                aws_specific_param_fzf.append_fzf(
                    f"SubnetId: {subnet['SubnetId']}")
                aws_specific_param_fzf.append_fzf(2*' ')
                aws_specific_param_fzf.append_fzf(
                    f"AvailabilityZone: {subnet['AvailabilityZone']}")
                aws_specific_param_fzf.append_fzf(2*' ')
                aws_specific_param_fzf.append_fzf(
                    f"CidrBlock: {subnet['CidrBlock']}")
                aws_specific_param_fzf.append_fzf('\n')

        elif type_name == 'AWS::EC2::Volume::Id':
            response = ec2.describe_volumes()
            for volume in response['Volumes']:
                aws_specific_param_fzf.append_fzf(
                    f"VolumeId: {volume['VolumeId']}"),
                if 'Tags' in volume and check_dict_value_in_list('Name', volume['Tags'], 'Key'):
                    aws_specific_param_fzf.append_fzf(2*' ')
                    aws_specific_param_fzf.append_fzf(
                        f"Name: {search_dict_in_list('Name', volume['Tags'], 'Key')['Value']}")
                aws_specific_param_fzf.append_fzf('\n')

        elif type_name == 'AWS::EC2::VPC::Id':
            response = ec2.describe_vpcs()
            for vpc in response['Vpcs']:
                aws_specific_param_fzf.append_fzf(f"VpcId: {vpc['VpcId']}")
                aws_specific_param_fzf.append_fzf(2*' ')
                aws_specific_param_fzf.append_fzf(
                    f"InstanceTenancy: {vpc['InstanceTenancy']}")
                aws_specific_param_fzf.append_fzf(2*' ')
                aws_specific_param_fzf.append_fzf(
                    f"CidrBlock: {vpc['CidrBlock']}")
                aws_specific_param_fzf.append_fzf('\n')

        elif type_name == 'AWS::Route53::HostedZone::Id':
            response = route53.list_hosted_zones()
            print(response)
            for hosted_zone in response['HostedZones']:
                aws_specific_param_fzf.append_fzf(
                    f"HostedZoneId: {hosted_zone['Id']}")
                aws_specific_param_fzf.append_fzf(2*' ')
                aws_specific_param_fzf.append_fzf(
                    f"Name: {hosted_zone['Name']}")
                aws_specific_param_fzf.append_fzf('\n')

        # get the selection from fzf
        selected_aws_value = aws_specific_param_fzf.execute_fzf(
            empty_allow=True)
        return selected_aws_value
    except ClientError as e:
        print(e)


# process the template file parameters
def process_stack_params(parameters):
    print('Enter parameters specified in your template below')
    # prepare array
    create_parameters = []
    for ParameterKey in parameters:
        # seperater
        print(80*'-')
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
        if parameter_type == 'List<Number>' or parameter_type == 'CommaDelimitedList':
            print(
                'For list type parameters, use comma to sperate items(e.g. values: value1, value2)')

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

        if type(ParameterValue) is list:
            ParameterValue = ','.join(ParameterValue)
            create_parameters.append(
                {'ParameterKey': ParameterKey, 'ParameterValue': ParameterValue})
        else:
            create_parameters.append(
                {'ParameterKey': ParameterKey, 'ParameterValue': ParameterValue})
    return create_parameters
