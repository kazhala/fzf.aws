"""contains funtions related to processing a new template"""
import boto3
import yaml
import json
import re
from botocore.exceptions import ClientError
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.util import remove_dict_from_list, search_dict_in_list, check_dict_value_in_list

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
    'List<AWS::EC2::AvailabilityZone::Name>',
    'List<AWS::EC2::Instance::Id>',
    'List<AWS::EC2::SecurityGroup::GroupName>',
    'List<AWS::EC2::SecurityGroup::Id>',
    'List<AWS::EC2::Subnet::Id>',
    'List<AWS::EC2::Volume::Id>',
    'List<AWS::EC2::VPC::Id>',
    'List<AWS::Route53::HostedZone::Id>'
]


def process_yaml_file(path):
    """read yaml file and return the file body"""
    with open(path, 'r') as body:
        # read all data into template_body for boto3 param
        body = body.read()
        # load yaml into pythong dict
        formated_body = yaml.safe_load(body)
        return {'body': body, 'dictBody': formated_body}


def process_json_file(path):
    """read the json file and return the file body"""
    with open(path, 'r') as body:
        # read raw body
        body = body.read()
        formated_body = json.loads(body)
        return {'body': body, 'dictBody': formated_body}


def process_yaml_body(file_body):
    """process the yaml body"""
    return yaml.safe_load(file_body)


def process_json_body(file_body):
    """process the json body"""
    return json.loads(file_body)


# handler if parameter type is a list type
def get_list_param_value(type_name):
    """handler if parameter type is a list type

    Args:
        type_name: string, type of the parameter
    Returns:
        processed list of selection from the user
        example:
            ['value', 'value']
    """

    try:
        fzf = Pyfzf()
        if type_name == 'List<AWS::EC2::AvailabilityZone::Name>':
            response = ec2.describe_availability_zones()
            response_list = response['AvailabilityZones']
            return fzf.process_list(response_list, 'ZoneName', multi_select=True)
        elif type_name == 'List<AWS::EC2::Instance::Id>':
            response = ec2.describe_instances()
            raw_response_list = response['Reservations']
            response_list = []
            for item in raw_response_list:
                response_list.append(
                    {'InstanceId': item['Instances'][0]['InstanceId'], 'Name': get_name_tag(item['Instances'][0])})
            return fzf.process_list(response_list, 'InstanceId', 'Name', multi_select=True)
        elif type_name == 'List<AWS::EC2::SecurityGroup::GroupName>':
            response = ec2.describe_security_groups()
            response_list = response['SecurityGroups']
            for sg in response_list:
                sg['Name'] = get_name_tag(sg)
            return fzf.process_list(response_list, 'GroupName', multi_select=True)
        elif type_name == 'List<AWS::EC2::SecurityGroup::Id>':
            response = ec2.describe_security_groups()
            response_list = response['SecurityGroups']
            for sg in response_list:
                sg['Name'] = get_name_tag(sg)
            return fzf.process_list(response_list, 'GroupId', 'GroupName', 'Name', multi_select=True)
        elif type_name == 'List<AWS::EC2::Subnet::Id>':
            response = ec2.describe_subnets()
            response_list = response['Subnets']
            for subnet in response_list:
                subnet['Name'] = get_name_tag(subnet)
            return fzf.process_list(response_list, 'SubnetId', 'AvailabilityZone', 'CidrBlock', 'Name', multi_select=True)
        elif type_name == 'List<AWS::EC2::Volume::Id>':
            response = ec2.describe_volumes()
            response_list = response['Volumes']
            for volume in response_list:
                volume['Name'] = get_name_tag(volume)
            return fzf.process_list(response_list, 'VolumeId', 'Name', multi_select=True)
        elif type_name == 'List<AWS::EC2::VPC::Id>':
            response = ec2.describe_vpcs()
            response_list = response['Vpcs']
            for vpc in response_list:
                vpc['Name'] = get_name_tag(vpc)
            return fzf.process_list(response_list, 'VpcId', 'IsDefault', 'CidrBlock', 'Name', multi_select=True)
        elif type_name == 'List<AWS::Route53::HostedZone::Id>':
            response = route53.list_hosted_zones()
            response_list = process_hosted_zone(response['HostedZones'])
            return fzf.process_list(response_list, 'Id', 'Name', multi_select=True)

    except ClientError as e:
        print(e)


def get_name_tag(list_item):
    """get the name tag of the item"""
    if 'Tags' in list_item and check_dict_value_in_list('Name', list_item['Tags'], 'Key'):
        return search_dict_in_list(
            'Name', list_item['Tags'], 'Key')['Value']
    else:
        return 'N/A'


def process_hosted_zone(hostedzone_list):
    """process hostedzone as the response is not raw id"""
    id_list = []
    id_pattern = r'/hostedzone/(?P<id>.*)$'
    for hosted_zone in hostedzone_list:
        raw_zone_id = re.search(
            id_pattern, hosted_zone['Id']).group('id')
        id_list.append(
            {'Id': raw_zone_id, 'Name': hosted_zone['Name']})
    return id_list


def get_selected_param_value(type_name):
    """use fzf to display aws specific parameters

    Args:
        type_name: string, name of the parameter
    Returns:
        A string/int of the selected value, require convert to string before
        giving it boto3
    """

    try:
        fzf = Pyfzf()
        if type_name == 'AWS::EC2::KeyPair::KeyName':
            response = ec2.describe_key_pairs()
            response_list = response['KeyPairs']
            return fzf.process_list(response_list, 'KeyName')
        elif type_name == 'AWS::EC2::SecurityGroup::Id':
            response = ec2.describe_security_groups()
            response_list = response['SecurityGroups']
            for sg in response['SecurityGroups']:
                sg['Name'] = get_name_tag(sg)
            return fzf.process_list(response_list, 'GroupId', 'GroupName', 'Name')
        elif type_name == 'AWS::EC2::AvailabilityZone::Name':
            response = ec2.describe_availability_zones()
            response_list = response['AvailabilityZones']
            return fzf.process_list(response_list, 'ZoneName')
        elif type_name == 'AWS::EC2::Instance::Id':
            response = ec2.describe_instances()
            response_list = []
            for instance in response['Reservations']:
                response_list.append({
                    'InstanceId': instance['Instances'][0]['InstanceId'],
                    'Name': get_name_tag(instance['Instances'][0])
                })
            return fzf.process_list(response_list, 'InstanceId', 'Name')
        elif type_name == 'AWS::EC2::SecurityGroup::GroupName':
            response = ec2.describe_security_groups()
            response_list = response['SecurityGroups']
            for sg in response['SecurityGroups']:
                sg['Name'] = get_name_tag(sg)
            return fzf.process_list(response_list, 'GroupName', 'Name')
        elif type_name == 'AWS::EC2::Subnet::Id':
            response = ec2.describe_subnets()
            response_list = response['Subnets']
            for subnet in response['Subnets']:
                subnet['Name'] = get_name_tag(subnet)
            return fzf.process_list(response_list, 'SubnetId', 'AvailabilityZone', 'CidrBlock', 'Name')
        elif type_name == 'AWS::EC2::Volume::Id':
            response = ec2.describe_volumes()
            response_list = response['Volumes']
            for volume in response['Volumes']:
                volume['Name'] = get_name_tag(volume)
            return fzf.process_list(response_list, 'VolumeId', 'Name')
        elif type_name == 'AWS::EC2::VPC::Id':
            response = ec2.describe_vpcs()
            response_list = response['Vpcs']
            for vpc in response['Vpcs']:
                vpc['Name'] = get_name_tag(vpc)
            return fzf.process_list(response_list, 'VpcId', 'IsDefault', 'CidrBlock', 'Name')
        elif type_name == 'AWS::Route53::HostedZone::Id':
            response = route53.list_hosted_zones()
            response_list = process_hosted_zone(response['HostedZones'])
            return fzf.process_list(response_list, 'Id', 'Name')

    except ClientError as e:
        print(e)


def get_user_input(parameters, ParameterKey, parameter_type, value_type=None, default=None):
    """get user input

    Args:
        parameters: list, the entire list of the parameters
        ParameterKey: string, the key of the current parameter
        parameter_type: string, type of hte parameter
        value_type: string('Default|Original'), determine if the current action is udpate or new creation or default value
        default: the default value or old value
    Returns:
        string, return the user selection through fzf or just python input
    """

    # execute fzf if allowed_value array exists
    if 'AllowedValues' in parameters[ParameterKey]:
        if value_type:
            print(
                f"Choose a value for {ParameterKey}({value_type}: {default})")
        else:
            print(f'Choose a value for {ParameterKey}:')
        choose_value_fzf = Pyfzf()
        for allowed_value in parameters[ParameterKey]['AllowedValues']:
            choose_value_fzf.append_fzf(allowed_value)
            choose_value_fzf.append_fzf('\n')
        user_input = choose_value_fzf.execute_fzf(
            empty_allow=True, print_col=1)
    else:
        if parameter_type in aws_specific_param:
            if value_type:
                print(f"{value_type}: {default}")
            user_input = get_selected_param_value(parameter_type)
        elif parameter_type in aws_specific_param_list:
            user_input = get_list_param_value(parameter_type)
        else:
            if not value_type:
                user_input = input(f'{ParameterKey}: ')
            # happens when there is a default value
            elif value_type == 'Default':
                user_input = input(
                    f'{ParameterKey}(Default: {default}): ')
            # happens when updating stack with replace option set
            # display previous or even use previous value for better experience
            elif value_type == 'Original':
                user_input = input(
                    f'{ParameterKey}(Original: {default}): ')
    if not user_input and default:
        return default
    elif user_input == "''":
        return ''
    elif user_input == '""':
        return ''
    else:
        return user_input


def process_stack_params(parameters, oldParameters=None):
    """process the template file parameters

    Args:
        parameters: list, entire parameter from boto3 response
        oldParameters: list, if updating, pass in oldParameters
    Returns:
        list of dict with value {'ParameterKey': value, 'ParameterValue': value}
    """

    if not oldParameters:
        oldParameters = dict()
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

        # update with replace current stack
        if check_dict_value_in_list(ParameterKey, oldParameters, 'ParameterKey'):
            original_value = search_dict_in_list(
                ParameterKey, oldParameters, 'ParameterKey')['ParameterValue']
            ParameterValue = get_user_input(
                parameters, ParameterKey, parameter_type, 'Original', original_value)

        # if default value exist
        elif 'Default' in parameters[ParameterKey]:
            default_value = parameters[ParameterKey]['Default']
            ParameterValue = get_user_input(
                parameters, ParameterKey, parameter_type, 'Default', default_value)

        # no default value
        else:
            ParameterValue = get_user_input(
                parameters, ParameterKey, parameter_type)

        if type(ParameterValue) is list:
            ParameterValue = ','.join(str(ParameterValue))
            create_parameters.append(
                {'ParameterKey': ParameterKey, 'ParameterValue': ParameterValue})
        else:
            create_parameters.append(
                {'ParameterKey': ParameterKey, 'ParameterValue': str(ParameterValue)})
    return create_parameters
