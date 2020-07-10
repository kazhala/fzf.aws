"""This module contains a single function to display information related to ec2."""
import json
from typing import Union

from fzfaws.ec2 import EC2


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
    subnetid: bool = False,
    volumeid: bool = False,
    vpcid: bool = False,
    vpc: bool = False,
    volume: bool = False,
    sg: bool = False,
    subnet: bool = False,
) -> None:
    """Display information about the instance.

    :param profile: profile to use for this operation
    :type profile: Union[bool, str], optional
    :param region: region to use for this operation
    :type region: Union[bool, str], optional
    :param ipv4: print instance ipv4 address
    :type ipv4: bool, optional
    :param privateip: print private ip address of the instance
    :type privateip: bool, optional
    :param dns: print dns of the instance
    :type dns: bool, optional
    :param az: print availability zone of instance
    :type az: bool, optional
    :param keyname: print keyname of the instance
    :type keyname: bool, optional
    :param instanceid: print instance id of the instance
    :type instanceid: bool, optional
    :param sgname: print selected security group name
    :type sgname: bool, optional
    :param sgid: print selected security group id
    :type sgid: bool, optional
    :param subnetid: print selected subnet id
    :type subnetid: bool, optional
    :param volumeid: print selected volume id
    :type volumeid: bool, optional
    :param vpcid: print selected vpc id
    :type vpcid: bool, optional
    :param vpc: print information about vpc instead of ec2
    :type vpc: bool, optional
    :param volume: print information about volume instead of ec2
    :type volume: bool, optional
    :param sg: print information about security group instead of ec2
    :type sg: bool, optional
    :param subet: print information about subnet instead of ec2
    :type subet: bool, optional
    :raises SystemExit: when the response is empty
    """
    ec2 = EC2(profile, region)

    if sg or sgid or sgname:
        if not sgid and not sgname:
            result = ec2.get_security_groups(multi_select=True, return_attr="id")
            if result:
                response = ec2.client.describe_security_groups(GroupIds=result)
                dump_response(response)
        else:
            if sgid:
                result = ec2.get_security_groups(multi_select=True, return_attr="id")
                for item in result:
                    print(item)
            if sgname:
                result = ec2.get_security_groups(multi_select=True, return_attr="name")
                for item in result:
                    print(item)
    elif subnet or subnetid:
        result = ec2.get_subnet_id(multi_select=True)
        if not subnetid and result:
            response = ec2.client.describe_subnets(SubnetIds=result)
            dump_response(response)
        else:
            for item in result:
                print(item)
    elif volume or volumeid:
        result = ec2.get_volume_id(multi_select=True)
        if not volumeid and result:
            response = ec2.client.describe_volumes(VolumeIds=result)
            dump_response(response)
        else:
            for item in result:
                print(item)
    elif vpc or vpcid:
        result = ec2.get_vpc_id(multi_select=True)
        if not vpcid and result:
            response = ec2.client.describe_vpcs(VpcIds=result)
            dump_response(response)
        else:
            for item in result:
                print(item)

    else:
        ec2.set_ec2_instance()
        if (
            not ipv4
            and not privateip
            and not dns
            and not az
            and not keyname
            and not instanceid
        ):
            response = ec2.client.describe_instances(InstanceIds=ec2.instance_ids)
            dump_response(response)
        else:
            for instance in ec2.instance_list:
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


def dump_response(response: dict) -> None:
    """Dump the json response."""
    response.pop("ResponseMetadata", None)
    print(json.dumps(response, indent=4, default=str))
