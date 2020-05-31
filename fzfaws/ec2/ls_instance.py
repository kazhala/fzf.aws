"""ls instance to show basic information

list instance and describe instance
"""
import json
from fzfaws.ec2 import EC2
from typing import Union


def ls_instance(
    profile: Union[str, bool] = False,
    region: Union[str, bool] = False,
    ipv4: bool = False,
    privateip: bool = False,
    dns: bool = False,
    az: bool = False,
    keyname: bool = False,
    instanceid: bool = False,
    sgname: bool = False,
    sgid: bool = False,
) -> None:
    """display information about the instance

    :param profile: profile to use for this operation
    :type profile: Union[bool, str], optional
    :param region: region to use for this operation
    :type region: Union[bool, str], optional
    :raises SystemExit: when the response is empty
    """

    ec2 = EC2(profile, region)
    if sgname or sgid:
        if sgid:
            result = ec2.get_security_groups(multi_select=True, return_attr="id")
            print(result[0] if result else "")
        if sgname:
            result = ec2.get_security_groups(multi_select=True, return_attr="name")
            print(result[0] if result else "")
    else:
        ec2.set_ec2_instance()
        response = ec2.client.describe_instances(InstanceIds=ec2.instance_ids)
        response.pop("ResponseMetadata", None)
        if (
            not ipv4
            and not privateip
            and not dns
            and not az
            and not keyname
            and not instanceid
        ):
            print(json.dumps(response, indent=4, default=str))
        else:
            if not response["Reservations"]:
                raise SystemExit
            for instance in response["Reservations"][0]["Instances"]:
                if ipv4:
                    print(instance.get("PublicIpAddress"))
                if privateip:
                    print(instance.get("PrivateIpAddress"))
                if dns:
                    print(instance.get("PublicDnsName"))
                if az:
                    print(instance.get("Placement", {}).get("AvailabilityZone"))
                if keyname:
                    print(instance.get("KeyName"))
                if instanceid:
                    print(instance.get("InstanceId"))
