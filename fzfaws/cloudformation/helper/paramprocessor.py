"""Contains ParamProcessor helper class.

Used to process parameter in template for cloudformation update/changeset/create stack.
"""
from typing import Any, Dict, List, Optional, Union

from fzfaws.ec2 import EC2
from fzfaws.route53 import Route53
from fzfaws.utils import Pyfzf, Spinner, check_dict_value_in_list, search_dict_in_list


class ParamProcessor:
    """Process cloudformation template params.

    Utilizing fzf and boto3 to give better experience of entering params
    for cloudformation.

    :param profile: use a different profile for this operation
    :type profile: Union[str, bool], optional
    :param region: use a different region for this operation
    :type region: Union[str, bool], optional
    :param params: cloudformation parameter to process
    :type params: dict, optional
    :param original_params: original params to display during update stack or changeset stack
    :type original_params: List[dict], optional
    """

    def __init__(
        self,
        profile: Optional[Union[str, bool]] = None,
        region: Optional[Union[str, bool]] = None,
        params: Dict[str, Any] = None,
        original_params: List[Dict[str, Any]] = None,
    ) -> None:
        """Construct the instance."""
        if params == None:
            params = {}
        if original_params == None:
            original_params = []
        self.ec2 = EC2(profile, region)
        self.route53 = Route53(profile, region)
        self.params: Dict[str, Any] = params
        self.original_params: List[Dict[str, Any]] = original_params
        self.processed_params: List[Dict[str, Any]] = []
        self._aws_specific_param: List[str] = [
            "AWS::EC2::AvailabilityZone::Name",
            "AWS::EC2::Instance::Id",
            "AWS::EC2::KeyPair::KeyName",
            "AWS::EC2::SecurityGroup::GroupName",
            "AWS::EC2::SecurityGroup::Id",
            "AWS::EC2::Subnet::Id",
            "AWS::EC2::Volume::Id",
            "AWS::EC2::VPC::Id",
            "AWS::Route53::HostedZone::Id",
        ]
        self._aws_specific_list_param: List[str] = [
            "List<AWS::EC2::AvailabilityZone::Name>",
            "List<AWS::EC2::Instance::Id>",
            "List<AWS::EC2::SecurityGroup::GroupName>",
            "List<AWS::EC2::SecurityGroup::Id>",
            "List<AWS::EC2::Subnet::Id>",
            "List<AWS::EC2::Volume::Id>",
            "List<AWS::EC2::VPC::Id>",
            "List<AWS::Route53::HostedZone::Id>",
        ]

    def process_stack_params(self) -> None:
        """Process the template file parameters.

        Loop through the keys in the loaded dict object of params and leverage
        self._get_user_input to get user input through fzf or cmd input
        """
        print("Enter parameters specified in your template below")

        for parameter_key in self.params:
            print(80 * "-")
            default_value: str = ""
            param_header: str = ""

            if "Description" in self.params[parameter_key]:
                param_header += (
                    "Description: %s\n" % self.params[parameter_key]["Description"]
                )
            if "ConstraintDescription" in self.params[parameter_key]:
                param_header += (
                    "ConstraintDescription: %s\n"
                    % self.params[parameter_key]["ConstraintDescription"]
                )
            if "AllowedPattern" in self.params[parameter_key]:
                param_header += (
                    "AllowedPattern: %s\n"
                    % self.params[parameter_key]["AllowedPattern"]
                )
            parameter_type: str = self.params[parameter_key]["Type"]
            param_header += "Type: %s\n" % parameter_type
            if (
                parameter_type == "List<Number>"
                or parameter_type == "CommaDelimitedList"
            ):
                param_header += "For list type parameters, use comma to sperate items(e.g. values: value1, value2)"

            if check_dict_value_in_list(
                parameter_key, self.original_params, "ParameterKey"
            ):
                # check if there is original value i.e. udpating the stack
                original_value: str = search_dict_in_list(
                    parameter_key, self.original_params, "ParameterKey"
                ).get("ParameterValue", "")
                parameter_value = self._get_user_input(
                    parameter_key,
                    parameter_type,
                    param_header,
                    "Original",
                    original_value,
                )
            elif "Default" in self.params[parameter_key]:
                # if default value exist
                default_value = self.params[parameter_key]["Default"]
                parameter_value = self._get_user_input(
                    parameter_key,
                    parameter_type,
                    param_header,
                    "Default",
                    default_value,
                )
            else:
                # no default value
                parameter_value = self._get_user_input(
                    parameter_key, parameter_type, param_header
                )

            if type(parameter_value) is list:
                # cloudformation only accept comma delimited list for list items
                parameter_value = ",".join(parameter_value)
                self.processed_params.append(
                    {"ParameterKey": parameter_key, "ParameterValue": parameter_value}
                )
            else:
                self.processed_params.append(
                    {
                        "ParameterKey": parameter_key,
                        "ParameterValue": str(parameter_value),
                    }
                )
            if (
                "AllowedValues" in self.params[parameter_key]
                or parameter_type in self._aws_specific_param
                or parameter_type in self._aws_specific_list_param
            ):
                # because list items and fzf input information are displayed in fzf header
                # it's hard for user to track what they have gone through
                # hence printing the header information to terminal as well
                print(param_header.rstrip())
            print("ParameterValue: %s" % parameter_value)

    def _get_user_input(
        self,
        parameter_key: str,
        parameter_type: str,
        param_header: str,
        value_type: str = None,
        default: str = None,
    ) -> Union[str, List[str]]:
        """Get user input.

        :param parameter_key: the current parameter key to obtain user input 
        :type parameter_key: str
        :param parameter_type: type of the parameter
        :type parameter_type: str
        :param param_header: information about current parameter
        :type param_header: str
        :param value_type: determine if the current action is update or new creation ('Default|Original')
        :type value_type: str, optional
        :param default: default value of params or orignal value
        :type default: str, optional
        :return: return the user selection through fzf or python input
        :rtype: Union[str, List[str]]
        """
        user_input: Union[str, List[str]] = ""

        # execute fzf if allowed_value array exists
        if "AllowedValues" in self.params[parameter_key]:
            param_header += self._print_parameter_key(
                parameter_key, value_type, default
            )
            fzf = Pyfzf()
            for allowed_value in self.params[parameter_key]["AllowedValues"]:
                fzf.append_fzf("%s\n" % allowed_value)
            user_input = fzf.execute_fzf(
                empty_allow=True, print_col=1, header=param_header
            )
        else:
            if parameter_type in self._aws_specific_param:
                param_header += self._print_parameter_key(
                    parameter_key, value_type, default
                )
                user_input = self._get_selected_param_value(
                    parameter_type, param_header
                )
            elif parameter_type in self._aws_specific_list_param:
                param_header += self._print_parameter_key(
                    parameter_key, value_type, default
                )
                user_input = self._get_list_param_value(parameter_type, param_header)
            else:
                print(param_header.rstrip())
                if not value_type:
                    user_input = input("%s: " % parameter_key)
                elif value_type == "Default":
                    user_input = input("%s(Default: %s): " % (parameter_key, default))
                elif value_type == "Original":
                    user_input = input("%s(Original: %s): " % (parameter_key, default))
        if not user_input and default:
            return default
        elif user_input == "''":
            return ""
        elif user_input == '""':
            return ""
        else:
            return user_input

    def _print_parameter_key(
        self, parameter_key: str, value_type: str = None, default: str = None
    ) -> str:
        """Print parameter_key."""
        if value_type:
            return "Choose a value for %s(%s: %s)" % (
                parameter_key,
                value_type,
                default,
            )
        else:
            return "Choose a value for %s" % parameter_key

    def _get_selected_param_value(self, type_name: str, param_header: str) -> str:
        """Use fzf to display aws specific parameters.

        :param type_name: name of the parameter type
        :type type_name: str
        :param param_header: information about current parameter
        :type param_header: str
        :return: return the selected value 
        :rtype: str
        """
        fzf = Pyfzf()

        if type_name == "AWS::EC2::KeyPair::KeyName":
            with Spinner.spin(message="Fetching KeyPair ..."):
                response = self.ec2.client.describe_key_pairs()
                response_list = response["KeyPairs"]
            fzf.process_list(response_list, "KeyName", empty_allow=True)
        elif type_name == "AWS::EC2::SecurityGroup::Id":
            return str(self.ec2.get_security_groups(header=param_header))
        elif type_name == "AWS::EC2::AvailabilityZone::Name":
            with Spinner.spin(message="Fetching AvailabilityZones ..."):
                response = self.ec2.client.describe_availability_zones
                response_list = response.get("AvailabilityZones", [])
            fzf.process_list(response_list, "ZoneName", empty_allow=True)
        elif type_name == "AWS::EC2::Instance::Id":
            return str(self.ec2.get_instance_id(header=param_header))
        elif type_name == "AWS::EC2::SecurityGroup::GroupName":
            return str(
                self.ec2.get_security_groups(return_attr="name", header=param_header)
            )
        elif type_name == "AWS::EC2::Subnet::Id":
            return str(self.ec2.get_subnet_id(header=param_header))
        elif type_name == "AWS::EC2::Volume::Id":
            return str(self.ec2.get_volume_id(header=param_header))
        elif type_name == "AWS::EC2::VPC::Id":
            return str(self.ec2.get_vpc_id(header=param_header))
        elif type_name == "AWS::Route53::HostedZone::Id":
            self.route53.set_zone_id()
            return self.route53.zone_ids[0]
        return str(fzf.execute_fzf(empty_allow=True, header=param_header))

    def _get_list_param_value(self, type_name: str, param_header: str) -> List[str]:
        """Handle operation if parameter type is a list type.

        This function is almost the same as _get_selected_param_value besides its
        handling list type rather than single vaiable type.

        :param type_name: name of the type of the parameter
        :type type_name: str
        :param param_header: information about the current parameter
        :type param_header: str
        :return: processed list of selection from the user
        :rtype: List[str]
        """
        fzf = Pyfzf()

        if type_name == "List<AWS::EC2::AvailabilityZone::Name>":
            with Spinner.spin(message="Fetching AvailabilityZones ..."):
                response = self.ec2.client.describe_availability_zones()
                response_list = response["AvailabilityZones"]
            fzf.process_list(response_list, "ZoneName", empty_allow=True)
        elif type_name == "List<AWS::EC2::Instance::Id>":
            return list(
                self.ec2.get_instance_id(multi_select=True, header=param_header)
            )
        elif type_name == "List<AWS::EC2::SecurityGroup::GroupName>":
            return list(
                self.ec2.get_security_groups(
                    multi_select=True, return_attr="name", header=param_header
                )
            )
        elif type_name == "List<AWS::EC2::SecurityGroup::Id>":
            return list(
                self.ec2.get_security_groups(multi_select=True, header=param_header)
            )
        elif type_name == "List<AWS::EC2::Subnet::Id>":
            return list(self.ec2.get_subnet_id(multi_select=True, header=param_header))
        elif type_name == "List<AWS::EC2::Volume::Id>":
            return list(self.ec2.get_volume_id(multi_select=True, header=param_header))
        elif type_name == "List<AWS::EC2::VPC::Id>":
            return list(self.ec2.get_vpc_id(multi_select=True, header=param_header))
        elif type_name == "List<AWS::Route53::HostedZone::Id>":
            self.route53.set_zone_id(multi_select=True)
            return self.route53.zone_ids
        return list(
            fzf.execute_fzf(multi_select=True, empty_allow=True, header=param_header)
        )
