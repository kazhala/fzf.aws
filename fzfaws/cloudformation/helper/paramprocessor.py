"""contains funtions related to processing a new template"""
import boto3
import re
from botocore.exceptions import ClientError
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.util import search_dict_in_list, check_dict_value_in_list, get_name_tag
from fzfaws.ec2.ec2 import EC2


class ParamProcessor:
    """Process cloudformation template params

    utilizing fzf and boto3 to give better experience of entering params
    for cloudformation

    Attributes:
        ec2: object, a boto3 client init from EC2 class
        route53: object a boto3 client init from Route53 class
        params: dict, collection of parameter to process
        original_params: dict, original_value of the params during update
        processed_params: dict, process params thats ready to be consumed
        _aws_specific_param: list, list of aws param that should be catched
        _aws_specific_list_param: list, list of aws list param that should be catched
    """

    def __init__(self, profile=None, region=None, params=None, original_params=None):
        """init the ParamProcessor

        Args:
            params: dict, collection of parameter to process
            original_params: dict, original_value of the params during update
            profile: string or bool, use a different profile for this operation
            region: string or bool, use a different region for this operation
        """
        self.ec2 = EC2(profile, region).client
        self.route53 = boto3.client('route53')
        self.params = params
        self.original_params = original_params
        self.processed_params = []
        self._aws_specific_param = [
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
        self._aws_specific_list_param = [
            'List<AWS::EC2::AvailabilityZone::Name>',
            'List<AWS::EC2::Instance::Id>',
            'List<AWS::EC2::SecurityGroup::GroupName>',
            'List<AWS::EC2::SecurityGroup::Id>',
            'List<AWS::EC2::Subnet::Id>',
            'List<AWS::EC2::Volume::Id>',
            'List<AWS::EC2::VPC::Id>',
            'List<AWS::Route53::HostedZone::Id>'
        ]

    def process_stack_params(self):
        """process the template file parameters

        Args:
            parameters: list, entire parameter from boto3 response
            oldParameters: list, if updating, pass in oldParameters
        Returns:
            list of dict with value {'ParameterKey': value, 'ParameterValue': value}
        """

        if not self.original_params:
            self.original_params = dict()
        print('Enter parameters specified in your template below')
        for parameter_key in self.params:
            print(80*'-')
            default_value = ''

            # print some information
            if 'Description' in self.params[parameter_key]:
                print(
                    f"Description: {self.params[parameter_key]['Description']}")
            if 'ConstraintDescription' in self.params[parameter_key]:
                print(
                    f"ConstraintDescription: {self.params[parameter_key]['ConstraintDescription']}")
            if 'AllowedPattern' in self.params[parameter_key]:
                print(
                    f"AllowedPattern: {self.params[parameter_key]['AllowedPattern']}")
            parameter_type = self.params[parameter_key]['Type']
            print(f"Type: {parameter_type}")
            if parameter_type == 'List<Number>' or parameter_type == 'CommaDelimitedList':
                print(
                    'For list type parameters, use comma to sperate items(e.g. values: value1, value2)')

            if check_dict_value_in_list(parameter_key, self.original_params, 'ParameterKey'):
                # update with replace current stack flag
                original_value = search_dict_in_list(
                    parameter_key, self.original_params, 'ParameterKey')['ParameterValue']
                parameter_value = self._get_user_input(
                    parameter_key, parameter_type, 'Original', original_value)
            elif 'Default' in self.params[parameter_key]:
                # if default value exist
                default_value = self.params[parameter_key]['Default']
                parameter_value = self._get_user_input(
                    parameter_key, parameter_type, 'Default', default_value)
            else:
                # no default value
                parameter_value = self._get_user_input(
                    parameter_key, parameter_type)

            if type(parameter_value) is list:
                parameter_value = ','.join(parameter_value)
                self.processed_params.append(
                    {'ParameterKey': parameter_key, 'ParameterValue': parameter_value})
            else:
                self.processed_params.append(
                    {'ParameterKey': parameter_key, 'ParameterValue': str(parameter_value)})

    def _get_user_input(self, parameter_key, parameter_type, value_type=None, default=None):
        """get user input

        Args:
            parameters: list, the entire list of the parameters
            parameter_key: string, the key of the current parameter
            parameter_type: string, type of hte parameter
            value_type: string('Default|Original'), determine if the current action is udpate or new creation or default value
            default: the default value or old value
        Returns:
            string, return the user selection through fzf or just python input
        """

        # execute fzf if allowed_value array exists
        if 'AllowedValues' in self.params[parameter_key]:
            if value_type:
                print(
                    f"Choose a value for {parameter_key}({value_type}: {default})")
            else:
                print(f'Choose a value for {parameter_key}:')
            choose_value_fzf = Pyfzf()
            for allowed_value in self.params[parameter_key]['AllowedValues']:
                choose_value_fzf.append_fzf(allowed_value)
                choose_value_fzf.append_fzf('\n')
            user_input = choose_value_fzf.execute_fzf(
                empty_allow=True, print_col=1)
        else:
            if parameter_type in self._aws_specific_param:
                if value_type:
                    print(
                        f"Choose a value for {parameter_key}({value_type}: {default})")
                user_input = self._get_selected_param_value(parameter_type)
            elif parameter_type in self._aws_specific_list_param:
                if value_type:
                    print(
                        f"Choose a value for {parameter_key}({value_type}: {default})")
                user_input = self._get_list_param_value(parameter_type)
            else:
                if not value_type:
                    user_input = input(f'{parameter_key}: ')
                elif value_type == 'Default':
                    user_input = input(
                        f'{parameter_key}(Default: {default}): ')
                elif value_type == 'Original':
                    user_input = input(
                        f'{parameter_key}(Original: {default}): ')
        if not user_input and default:
            return default
        elif user_input == "''":
            return ''
        elif user_input == '""':
            return ''
        else:
            return user_input

    def _get_selected_param_value(self, type_name):
        """use fzf to display aws specific parameters

        Args:
            type_name: string, name of the parameter
        Returns:
            A string/int of the selected value, require convert to string before
            giving it boto3
        """

        fzf = Pyfzf()
        if type_name == 'AWS::EC2::KeyPair::KeyName':
            response = self.ec2.describe_key_pairs()
            response_list = response['KeyPairs']
            fzf.process_list(response_list, 'KeyName')
            return fzf.execute_fzf(empty_allow=True)
        elif type_name == 'AWS::EC2::SecurityGroup::Id':
            response = self.ec2.describe_security_groups()
            response_list = response['SecurityGroups']
            for sg in response['SecurityGroups']:
                sg['Name'] = get_name_tag(sg)
            fzf.process_list(response_list, 'GroupId', 'GroupName', 'Name')
            return fzf.execute_fzf(empty_allow=True)
        elif type_name == 'AWS::EC2::AvailabilityZone::Name':
            response = self.ec2.describe_availability_zones()
            response_list = response['AvailabilityZones']
            fzf.process_list(response_list, 'ZoneName')
            return fzf.execute_fzf(empty_allow=True)
        elif type_name == 'AWS::EC2::Instance::Id':
            response = self.ec2.describe_instances()
            response_list = []
            for instance in response['Reservations']:
                response_list.append({
                    'InstanceId': instance['Instances'][0]['InstanceId'],
                    'Name': get_name_tag(instance['Instances'][0])
                })
            fzf.process_list(response_list, 'InstanceId', 'Name')
            return fzf.execute_fzf(empty_allow=True)
        elif type_name == 'AWS::EC2::SecurityGroup::GroupName':
            response = self.ec2.describe_security_groups()
            response_list = response['SecurityGroups']
            for sg in response['SecurityGroups']:
                sg['Name'] = get_name_tag(sg)
            fzf.process_list(response_list, 'GroupName', 'Name')
            return fzf.execute_fzf(empty_allow=True)
        elif type_name == 'AWS::EC2::Subnet::Id':
            response = self.ec2.describe_subnets()
            response_list = response['Subnets']
            for subnet in response['Subnets']:
                subnet['Name'] = get_name_tag(subnet)
            fzf.process_list(response_list, 'SubnetId',
                             'AvailabilityZone', 'CidrBlock', 'Name')
            return fzf.execute_fzf(empty_allow=True)
        elif type_name == 'AWS::EC2::Volume::Id':
            response = self.ec2.describe_volumes()
            response_list = response['Volumes']
            for volume in response['Volumes']:
                volume['Name'] = get_name_tag(volume)
            fzf.process_list(response_list, 'VolumeId', 'Name')
            return fzf.execute_fzf(empty_allow=True)
        elif type_name == 'AWS::EC2::VPC::Id':
            response = self.ec2.describe_vpcs()
            response_list = response['Vpcs']
            for vpc in response['Vpcs']:
                vpc['Name'] = get_name_tag(vpc)
            fzf.process_list(response_list, 'VpcId',
                             'IsDefault', 'CidrBlock', 'Name')
            return fzf.execute_fzf(empty_allow=True)
        elif type_name == 'AWS::Route53::HostedZone::Id':
            response = self.route53.list_hosted_zones()
            response_list = self._process_hosted_zone(response['HostedZones'])
            fzf.process_list(response_list, 'Id', 'Name')
            return fzf.execute_fzf(empty_allow=True)

    # handler if parameter type is a list type

    def _get_list_param_value(self, type_name):
        """handler if parameter type is a list type

        Args:
            type_name: string, type of the parameter
        Returns:
            processed list of selection from the user
            example:
                ['value', 'value']
        """

        fzf = Pyfzf()
        if type_name == 'List<AWS::EC2::AvailabilityZone::Name>':
            response = self.ec2.describe_availability_zones()
            response_list = response['AvailabilityZones']
            fzf.process_list(response_list, 'ZoneName')
            return fzf.execute_fzf(multi_select=True, empty_allow=True)
        elif type_name == 'List<AWS::EC2::Instance::Id>':
            response = self.ec2.describe_instances()
            raw_response_list = response['Reservations']
            response_list = []
            for item in raw_response_list:
                response_list.append(
                    {'InstanceId': item['Instances'][0]['InstanceId'], 'Name': get_name_tag(item['Instances'][0])})
            fzf.process_list(response_list, 'InstanceId', 'Name')
            return fzf.execute_fzf(multi_select=True, empty_allow=True)
        elif type_name == 'List<AWS::EC2::SecurityGroup::GroupName>':
            response = self.ec2.describe_security_groups()
            response_list = response['SecurityGroups']
            for sg in response_list:
                sg['Name'] = get_name_tag(sg)
            fzf.process_list(response_list, 'GroupName')
            return fzf.execute_fzf(multi_select=True, empty_allow=True)
        elif type_name == 'List<AWS::EC2::SecurityGroup::Id>':
            response = self.ec2.describe_security_groups()
            response_list = response['SecurityGroups']
            for sg in response_list:
                sg['Name'] = get_name_tag(sg)
            fzf.process_list(response_list, 'GroupId', 'GroupName', 'Name')
            return fzf.execute_fzf(multi_select=True, empty_allow=True)
        elif type_name == 'List<AWS::EC2::Subnet::Id>':
            response = self.ec2.describe_subnets()
            response_list = response['Subnets']
            for subnet in response_list:
                subnet['Name'] = get_name_tag(subnet)
            fzf.process_list(response_list, 'SubnetId',
                             'AvailabilityZone', 'CidrBlock', 'Name')
            return fzf.execute_fzf(multi_select=True, empty_allow=True)
        elif type_name == 'List<AWS::EC2::Volume::Id>':
            response = self.ec2.describe_volumes()
            response_list = response['Volumes']
            for volume in response_list:
                volume['Name'] = get_name_tag(volume)
            fzf.process_list(response_list, 'VolumeId', 'Name')
            return fzf.execute_fzf(multi_select=True, empty_allow=True)
        elif type_name == 'List<AWS::EC2::VPC::Id>':
            response = self.ec2.describe_vpcs()
            response_list = response['Vpcs']
            for vpc in response_list:
                vpc['Name'] = get_name_tag(vpc)
            fzf.process_list(response_list, 'VpcId',
                             'IsDefault', 'CidrBlock', 'Name')
            return fzf.execute_fzf(multi_select=True, empty_allow=True)
        elif type_name == 'List<AWS::Route53::HostedZone::Id>':
            response = self.route53.list_hosted_zones()
            response_list = self._process_hosted_zone(response['HostedZones'])
            fzf.process_list(response_list, 'Id', 'Name')
            return fzf.execute_fzf(multi_select=True, empty_allow=True)

    def _process_hosted_zone(self, hostedzone_list):
        """process hostedzone as the response is not raw id"""
        id_list = []
        id_pattern = r'/hostedzone/(?P<id>.*)$'
        for hosted_zone in hostedzone_list:
            raw_zone_id = re.search(
                id_pattern, hosted_zone['Id']).group('id')
            id_list.append(
                {'Id': raw_zone_id, 'Name': hosted_zone['Name']})
        return id_list
