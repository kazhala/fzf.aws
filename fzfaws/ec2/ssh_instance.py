"""This module contains the ssh function.

Note: only ssh_instance should be import and used, other functions
are just helper function for ssh_instance.
"""
import os
import subprocess
from typing import Any, Dict, Union

from fzfaws.ec2 import EC2
from fzfaws.utils.exceptions import EC2Error

home = os.path.expanduser("~")


def check_instance_status(instance: Dict[str, Any]) -> None:
    """Check if instance is in running status.

    :param instance: instance details to be checked
    :type instance: dict
    """
    if instance["Status"] == "stopped":
        raise EC2Error(
            "%s is currently stopped, run faws ec2 start to start the instance"
            % instance["InstanceId"]
        )
    elif instance["Status"] != "running":
        raise EC2Error(
            "%s is still in %s state, please wait"
            % (instance["InstanceId"], instance["Status"])
        )


def get_instance_ip(instance: Dict[str, Any], ip_type: str = "dns") -> str:
    """Get instance ip.

    Using a fall back method to check PublicDnsName and them PublicIpAddress
    and finally the PrivateIpAddress.

    :param instance: instance detail
    :type instance: Dict[str, Any]
    :param ip_type: what types of ip to get
    :type ip_type: str, optional
    :return: selected instance ip address or dns address
    :rtype: str
    """
    if ip_type == "dns":
        if instance.get("PublicDnsName"):
            return instance["PublicDnsName"]
        else:
            ip_type = "public"
    if ip_type == "public":
        if instance.get("PublicIpAddress"):
            return instance["PublicIpAddress"]
        else:
            ip_type = "private"
    if ip_type == "private":
        if instance.get("PrivateIpAddress"):
            return instance["PrivateIpAddress"]
        raise EC2Error(
            "%s doesn't have an available ip associated, instance is likely not running"
        )
    return ""


def ssh_instance(
    profile: Union[str, bool] = False,
    region: Union[str, bool] = False,
    bastion: bool = False,
    username: str = "ec2-user",
    tunnel: Union[bool, str] = False,
    keypath: str = "",
) -> None:
    """Perform ssh operation into the ec2 instance.

    :param profile: profile to use for this operation
    :type profile: Union[bool, str], optional
    :param region: region to use for this operation
    :type region: Union[bool, str], optional
    :param bastion: use ssh forwading
    :type bastion: bool, optional
    :param username: username to ssh inot
    :type username: str, optional
    :param tunnel: connect to a instance through ssh tunnel, pass in str to specify username
    :type tunnel: Union[bool, str], optional
    :param keypath: path to key pem
    :type keypath: str, optional
    :raises EC2Error: the selected ec2 instance is not in running state or key pair not detected
    """
    ec2 = EC2(profile, region)
    ec2.set_ec2_instance(
        multi_select=False,
        header="select instance to connect"
        if not tunnel
        else "select jumpbox instance",
    )

    check_instance_status(ec2.instance_list[0])
    ssh_key_location: str = os.path.expanduser(
        os.getenv("FZFAWS_EC2_KEYPAIRS", default="~/.ssh")
    )
    os.chdir(ssh_key_location)
    ssh_key: str = os.path.join(
        ssh_key_location, "%s.pem" % ec2.instance_list[0].get("KeyName", "")
    ) if not keypath else keypath

    if not tunnel:
        instance_ip = get_instance_ip(ec2.instance_list[0])
        cmd_list: list = construct_normal_ssh(ssh_key, instance_ip, username, bastion)
    else:
        jumpbox_ip = get_instance_ip(ec2.instance_list[0])
        jumpbox_username = username
        print("Jumpbox instance is running")
        ec2.set_ec2_instance(
            multi_select=False, header="select the destination instance"
        )
        check_instance_status(ec2.instance_list[0])
        print("Instance is running, ready to connect")
        if type(tunnel) == str:
            dest_username = str(tunnel)
        else:
            dest_username = username
        dest_ip = get_instance_ip(ec2.instance_list[0])
        cmd_list: list = construct_tunnel_ssh(
            ssh_key, jumpbox_ip, jumpbox_username, dest_ip, dest_username,
        )

    ssh = subprocess.Popen(cmd_list, shell=False)
    # allow user input
    stdoutdata, stderrdata = ssh.communicate()
    if stdoutdata:
        print(stdoutdata)
    if stderrdata:
        print(stderrdata)


def construct_normal_ssh(
    ssh_key: str, instance_ip: str, username: str, bastion: bool
) -> list:
    """Construct ssh command for subprocess.

    :param ssh_key: ssh key path
    :type ssh_key: str
    :param instance_ip: ip of the instance
    :type instance_ip: list
    :param username: username to ssh inot
    :type username: str
    :param bastion: use ssh forwading
    :type bastion: bool
    :raises EC2Error: the selected ec2 instance is not in running state or key pair not detected
    :return: cmd list to ssh
    :rtype: list
    """
    print("Instance is running, ready to connect")

    # check for file existence
    if os.path.isfile(ssh_key):
        cmd_list: list = ["ssh"]
        if bastion:
            cmd_list.append("-A")
        # if for custom VPC doesn't have public dns name, use public ip address
        cmd_list.extend(
            ["-i", ssh_key, "%s@%s" % (username, instance_ip),]
        )
    else:
        raise EC2Error("Key pair not detected in the specified location")
    return cmd_list


def construct_tunnel_ssh(
    ssh_key: str,
    jumpbox_ip: str,
    jumpbox_username: str,
    dest_ip: str,
    dest_username: str,
) -> list:
    """Construct ssh tunnel command for subprocess.

    :param ssh_key: ssh key path
    :type ssh_key: str
    :param jumpbox_ip: ip of the instance
    :type jumpbox_ip: list
    :param jumpbox_username: username for jumpbox
    :type jumpbox_username: str
    :param dest_ip: ip of the destination instance
    :type dest_ip: list
    :param dest_username: username for destiantion
    :type dest_username: str
    :raises EC2Error: the selected ec2 instance is not in running state or key pair not detected
    :return: cmd list to ssh
    :rtype: list
    """
    if os.path.isfile(ssh_key):
        cmd_list: list = [
            "ssh",
            "-A",
            "-i",
            ssh_key,
            "%s@%s" % (jumpbox_username, jumpbox_ip),
            "-t",
            "ssh",
            "%s@%s" % (dest_username, dest_ip),
        ]
    else:
        raise EC2Error("Key pair not detected in the specified location")
    return cmd_list
