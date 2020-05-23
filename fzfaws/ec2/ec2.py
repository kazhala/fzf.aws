"""ec2 wrapper class

A simple wrapper class of ec2 to interact with boto3.client('ec2')
"""
from fzfaws.utils import BaseSession, Pyfzf, get_name_tag, search_dict_in_list, Spinner
from typing import Union, Optional


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
        self.instance_list: list = []
        self.instance_ids: list = []

    def set_ec2_instance(self, multi_select=True, header=None):
        # type: (bool) -> None
        """set ec2 instance for current operation

        :param multi_select: enable multi select
        :type multi_select: bool, optional
        :param header: helper information to display in fzf header
        :type header: str, optional
        """

        try:
            response_list = []  # type: list
            fzf = Pyfzf()
            spinner = Spinner(message="Fetching EC2 instances..")
            spinner.start()
            paginator = self.client.get_paginator("describe_instances")
            for result in paginator.paginate():
                response_list = []
                # prepare the list for fzf
                for instance in result["Reservations"]:
                    response_list.append(
                        {
                            "InstanceId": instance["Instances"][0].get("InstanceId"),
                            "InstanceType": instance["Instances"][0].get(
                                "InstanceType"
                            ),
                            "Status": instance["Instances"][0]["State"].get("Name"),
                            "Name": get_name_tag(instance["Instances"][0]),
                            "KeyName": instance["Instances"][0].get("KeyName", "N/A"),
                            "PublicDnsName": instance["Instances"][0].get(
                                "PublicDnsName", "N/A"
                            ),
                            "PublicIpAddress": instance["Instances"][0].get(
                                "PublicIpAddress", "N/A"
                            ),
                            "PrivateIpAddress": instance["Instances"][0].get(
                                "PrivateIpAddress", "N/A"
                            ),
                        }
                    )
                fzf.process_list(
                    response_list,
                    "InstanceId",
                    "Status",
                    "InstanceType",
                    "Name",
                    "KeyName",
                    "PublicDnsName",
                    "PublicIpAddress",
                    "PrivateIpAddress",
                )
            spinner.stop()
            selected_instance_ids = fzf.execute_fzf(
                multi_select=multi_select, header=header
            )

            if multi_select:
                self.instance_ids = list(selected_instance_ids)
                for instance in self.instance_ids:
                    self.instance_list.append(
                        search_dict_in_list(instance, response_list, "InstanceId")
                    )
            else:
                self.instance_ids.append(str(selected_instance_ids))
                self.instance_list.append(
                    search_dict_in_list(
                        selected_instance_ids, response_list, "InstanceId"
                    )
                )
        except:
            Spinner.clear_spinner()
            raise

    def print_instance_details(self):
        # type: () -> None
        """display information of selected instances

        call this method before calling boto3 to do any ec2 opeartion
        and get confirmation
        """
        for instance in self.instance_list:
            print(
                "InstanceId: %s  Name: %s" % (instance["InstanceId"], instance["Name"])
            )

    def wait(self, waiter_name, message=None, delay=15, attempts=40):
        # type: (str, str, int, int) -> None
        """wait for the operation to be completed

        Args:
            waiter_name: string, name from boto3 waiter
            message: string, message to display during loading
            delay: number, how long between each attempt
            attempts: number, max attempts, usually 60mins, so 30 * 120
        Returns:
            None
            will pause the program until finish or error raised
        """
        try:
            spinner = Spinner(message=message)
            spinner.start()
            waiter = self.client.get_waiter(waiter_name)
            waiter.wait(
                InstanceIds=self.instance_ids,
                WaiterConfig={"Delay": delay, "MaxAttempts": attempts},
            )
            spinner.stop()
        except:
            Spinner.clear_spinner()
            raise

    def get_security_groups(self, multi_select=False, return_attr="id", header=None):
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
        try:
            fzf = Pyfzf()
            spinner = Spinner(message="Fetching SecurityGroups..")
            spinner.start()
            paginator = self.client.get_paginator("describe_security_groups")
            for result in paginator.paginate():
                response_list = result["SecurityGroups"]
                for sg in response_list:
                    sg["Name"] = get_name_tag(sg)
                if return_attr == "id":
                    fzf.process_list(response_list, "GroupId", "GroupName", "Name")
                elif return_attr == "name":
                    fzf.process_list(response_list, "GroupName", "Name")
            spinner.stop()
            return fzf.execute_fzf(
                multi_select=multi_select, empty_allow=True, header=header
            )
        except:
            Spinner.clear_spinner()
            raise

    def get_instance_id(self, multi_select=False, header=None):
        """use paginator to get instance id and return it

        :param multi_select: allow multiple value selection
        :type multi_select: bool, optional
        :param header: header to display in fzf header
        :type header: str, optional
        :return: selected instance id
        :rtype: Union[str, list]
        """
        try:
            fzf = Pyfzf()
            spinner = Spinner(message="Fetching EC2 instances..")
            spinner.start()
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
            spinner.stop()
            return fzf.execute_fzf(
                multi_select=multi_select, empty_allow=True, header=header
            )
        except:
            Spinner.clear_spinner()
            raise

    def get_subnet_id(self, multi_select=False, header=None):
        """get user selected subnet id through fzf

        :param multi_select: allow multiple value selection
        :type multi_select: bool, optional
        :param header: header to display in fzf header
        :type header: str, optional
        :return: selected subnet id
        :rtype: Union[str, list]
        """
        try:
            fzf = Pyfzf()
            spinner = Spinner(message="Fetching Subnets..")
            spinner.start()
            paginator = self.client.get_paginator("describe_subnets")
            for result in paginator.paginate():
                response_list = result["Subnets"]
                for subnet in response_list:
                    subnet["Name"] = get_name_tag(subnet)
                fzf.process_list(
                    response_list, "SubnetId", "AvailabilityZone", "CidrBlock", "Name"
                )
            spinner.stop()
            return fzf.execute_fzf(
                multi_select=multi_select, empty_allow=True, header=header
            )
        except:
            Spinner.clear_spinner()
            raise

    def get_volume_id(self, multi_select=False, header=None):
        """get user selected volume id through fzf

        :param multi_select: allow multiple value selection
        :type multi_select: bool, optional
        :param header: header to display in fzf header
        :type header: str, optional
        :return: selected volume id
        :rtype: Union[str, list]
        """
        try:
            fzf = Pyfzf()
            spinner = Spinner(message="Fetching EBS volumes..")
            spinner.start()
            paginator = self.client.get_paginator("describe_volumes")
            for result in paginator.paginate():
                response_list = result["Volumes"]
                for volume in response_list:
                    volume["Name"] = get_name_tag(volume)
                fzf.process_list(response_list, "VolumeId", "Name")
            spinner.stop()
            return fzf.execute_fzf(
                multi_select=multi_select, empty_allow=True, header=header
            )
        except:
            Spinner.clear_spinner()
            raise

    def get_vpc_id(self, multi_select=False, header=None):
        """get user selected vpc id through fzf

        :param multi_select: allow multiple value selection
        :type multi_select: bool, optional
        :param header: header to display in fzf header
        :type header: str, optional
        :return: selected vpc id
        :rtype: Union[str, list]
        """
        try:
            fzf = Pyfzf()
            spinner = Spinner(message="Fetching VPCs..")
            spinner.start()
            paginator = self.client.get_paginator("describe_vpcs")
            for result in paginator.paginate():
                response_list = result["Vpcs"]
                for vpc in response_list:
                    vpc["Name"] = get_name_tag(vpc)
                fzf.process_list(
                    response_list, "VpcId", "IsDefault", "CidrBlock", "Name"
                )
            spinner.stop()
            return fzf.execute_fzf(
                empty_allow=True, multi_select=multi_select, header=header
            )
        except:
            Spinner.clear_spinner()
            raise
