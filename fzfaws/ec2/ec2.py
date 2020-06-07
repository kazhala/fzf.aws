"""ec2 wrapper class

A simple wrapper class of ec2 to interact with boto3.client('ec2')
"""
import os
import json
from fzfaws.utils import BaseSession, Pyfzf, get_name_tag, search_dict_in_list, Spinner
from typing import Dict, Generator, Union, Optional, List


class EC2(BaseSession):
    """handles operation for all ec2 related task with boto3.client('ec2')

    :param profile: profile to use for this operation
    :type profile: Union[bool, str]
    :param region: region to use for this operation
    :type region: Union[bool, str]
    """

    def __init__(
        self,
        profile: Optional[Union[str, bool]] = None,
        region: Optional[Union[str, bool]] = None,
    ) -> None:
        """constructor
        """
        super().__init__(profile=profile, region=region, service_name="ec2")
        self.instance_list: list = [{}]
        self.instance_ids: list = [""]

    def _instance_generator(
        self, instances: List[dict]
    ) -> Generator[Dict[str, str], None, None]:
        """get ec2 instance helper, format ec2 response and return generator

        :param instances: list of instance response from boto3
        :type instances: List[dict]
        :return: formatted dict of instance information in generator form
        :rtype: Generator[Dict[str,str], None, None]
        """
        for instance in instances:
            instance_information = {
                "InstanceId": instance["Instances"][0].get("InstanceId"),
                "InstanceType": instance["Instances"][0].get("InstanceType"),
                "Status": instance["Instances"][0]["State"].get("Name"),
                "Name": get_name_tag(instance["Instances"][0]),
                "KeyName": instance["Instances"][0].get("KeyName", "N/A"),
                "PublicDnsName": instance["Instances"][0].get("PublicDnsName", "N/A"),
                "PublicIpAddress": instance["Instances"][0].get(
                    "PublicIpAddress", "N/A"
                ),
                "PrivateIpAddress": instance["Instances"][0].get(
                    "PrivateIpAddress", "N/A"
                ),
            }
            yield instance_information

    def set_ec2_instance(self, multi_select: bool = True, header: str = None) -> None:
        """set ec2 instance for current operation

        :param multi_select: enable multi select
        :type multi_select: bool, optional
        :param header: helper information to display in fzf header
        :type header: str, optional
        """

        fzf = Pyfzf()
        with Spinner.spin(message="Fetching EC2 instances ..."):
            paginator = self.client.get_paginator("describe_instances")
            for result in paginator.paginate():
                response_generator = self._instance_generator(result["Reservations"])
                fzf.process_list(
                    response_generator,
                    "InstanceId",
                    "Status",
                    "InstanceType",
                    "Name",
                    "KeyName",
                    "PublicDnsName",
                    "PublicIpAddress",
                    "PrivateIpAddress",
                )
        selected_instance = fzf.execute_fzf(
            multi_select=multi_select, header=header, print_col=0
        )

        if multi_select:
            self.instance_ids[:] = []
            self.instance_list[:] = []
            for instance in selected_instance:
                instance_details = instance.split(" | ")
                self.instance_ids.append(instance_details[0].split(": ")[1])
                self.instance_list.append(
                    {
                        key_value.split(": ")[0]: key_value.split(": ")[1]
                        for key_value in instance_details
                    }
                )
        else:
            instance_details = str(selected_instance).split(" | ")
            self.instance_ids[:] = []
            self.instance_list[:] = []
            self.instance_ids.append(instance_details[0].split(": ")[1])
            self.instance_list.append(
                {
                    key_value.split(": ")[0]: key_value.split(": ")[1]
                    for key_value in instance_details
                }
            )

    def print_instance_details(self) -> None:
        """display information of selected instances

        call this method before calling boto3 to do any ec2 opeartion
        and get confirmation
        """
        for instance in self.instance_list:
            print(
                "InstanceId: %s  Name: %s" % (instance["InstanceId"], instance["Name"])
            )

    def wait(self, waiter_name: str, message: str = None) -> None:
        """wait for the operation to be completed

        :param waiter_name: name of boto3 waiter
        :type waiter_name: str
        :param message: message to display during loading
        :type message: str, optional
        """
        with Spinner.spin(message=message):
            waiter = self.client.get_waiter(waiter_name)
            waiter_config = os.getenv(
                "FZFAWS_EC2_WAITER", os.getenv("FZFAWS_GLOBAL_WAITER", "")
            )
            delay: int = 15
            max_attempts: int = 40
            if waiter_config:
                waiter_config = json.loads(waiter_config)
                delay = int(waiter_config.get("delay", 15))
                max_attempts = int(waiter_config.get("max_attempts", 40))
            waiter.wait(
                InstanceIds=self.instance_ids,
                WaiterConfig={"Delay": delay, "MaxAttempts": max_attempts},
            )

    def get_security_groups(
        self, multi_select: bool = False, return_attr: str = "id", header: str = None
    ) -> Union[str, list]:
        """use paginator to get the user selected security groups

        :param multi_select: allow multiple value selection
        :type multi_select: bool, optional
        :param return_attr: what attribute to return (id|name)
        :type return_attr: str, optional
        :param header: header to display in fzf
        :type header: str, optional
        :return: selected security groups/ids
        :rtype: Union[str, list]
        """
        fzf = Pyfzf()
        with Spinner.spin(message="Fetching SecurityGroups ..."):
            paginator = self.client.get_paginator("describe_security_groups")
            for result in paginator.paginate():
                response_list = result["SecurityGroups"]
                for sg in response_list:
                    sg["Name"] = get_name_tag(sg)
                if return_attr == "id":
                    fzf.process_list(response_list, "GroupId", "GroupName", "Name")
                elif return_attr == "name":
                    fzf.process_list(response_list, "GroupName", "Name")
        return fzf.execute_fzf(
            multi_select=multi_select, empty_allow=True, header=header
        )

    def get_instance_id(
        self, multi_select: bool = False, header: str = None
    ) -> Union[str, list]:
        """use paginator to get instance id and return it

        :param multi_select: allow multiple value selection
        :type multi_select: bool, optional
        :param header: header to display in fzf header
        :type header: str, optional
        :return: selected instance id
        :rtype: Union[str, list]
        """
        fzf = Pyfzf()
        with Spinner.spin(message="Fetching EC2 instances ..."):
            paginator = self.client.get_paginator("describe_instances")
            for result in paginator.paginate():
                response_list = []
                for instance in result["Reservations"]:
                    response_list.append(
                        {
                            "InstanceId": instance["Instances"][0]["InstanceId"],
                            "Name": get_name_tag(instance["Instances"][0]),
                        }
                    )
                fzf.process_list(response_list, "InstanceId", "Name")
        return fzf.execute_fzf(
            multi_select=multi_select, empty_allow=True, header=header
        )

    def get_subnet_id(
        self, multi_select: bool = False, header: str = None
    ) -> Union[str, list]:
        """get user selected subnet id through fzf

        :param multi_select: allow multiple value selection
        :type multi_select: bool, optional
        :param header: header to display in fzf header
        :type header: str, optional
        :return: selected subnet id
        :rtype: Union[str, list]
        """
        fzf = Pyfzf()
        with Spinner.spin(message="Fetching Subnets ..."):
            paginator = self.client.get_paginator("describe_subnets")
            for result in paginator.paginate():
                response_list = result["Subnets"]
                for subnet in response_list:
                    subnet["Name"] = get_name_tag(subnet)
                fzf.process_list(
                    response_list, "SubnetId", "AvailabilityZone", "CidrBlock", "Name"
                )
        return fzf.execute_fzf(
            multi_select=multi_select, empty_allow=True, header=header
        )

    def get_volume_id(
        self, multi_select: bool = False, header: str = None
    ) -> Union[str, list]:
        """get user selected volume id through fzf

        :param multi_select: allow multiple value selection
        :type multi_select: bool, optional
        :param header: header to display in fzf header
        :type header: str, optional
        :return: selected volume id
        :rtype: Union[str, list]
        """
        fzf = Pyfzf()
        with Spinner.spin(message="Fetching EBS volumes ..."):
            paginator = self.client.get_paginator("describe_volumes")
            for result in paginator.paginate():
                response_list = result["Volumes"]
                for volume in response_list:
                    volume["Name"] = get_name_tag(volume)
                fzf.process_list(response_list, "VolumeId", "Name")
        return fzf.execute_fzf(
            multi_select=multi_select, empty_allow=True, header=header
        )

    def get_vpc_id(
        self, multi_select: bool = False, header: str = None
    ) -> Union[str, list]:
        """get user selected vpc id through fzf

        :param multi_select: allow multiple value selection
        :type multi_select: bool, optional
        :param header: header to display in fzf header
        :type header: str, optional
        :return: selected vpc id
        :rtype: Union[str, list]
        """
        fzf = Pyfzf()
        with Spinner.spin(message="Fetching VPCs ..."):
            paginator = self.client.get_paginator("describe_vpcs")
            for result in paginator.paginate():
                response_list = result["Vpcs"]
                for vpc in response_list:
                    vpc["Name"] = get_name_tag(vpc)
                fzf.process_list(
                    response_list, "VpcId", "IsDefault", "CidrBlock", "Name"
                )
        return fzf.execute_fzf(
            empty_allow=True, multi_select=multi_select, header=header
        )
