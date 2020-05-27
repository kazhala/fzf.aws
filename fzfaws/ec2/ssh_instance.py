"""ssh into the instance

perform ssh operation
"""
import os
import subprocess
from fzfaws.ec2 import EC2
from fzfaws.utils.exceptions import EC2Error
from typing import Optional, Union

home = os.path.expanduser("~")


def check_instance_status(instance: dict) -> None:
    """check if instance is in running status

    :param instance: instance details to be checked
    :type instance: dict
    """
    if instance["Status"] == "stopped":
        raise EC2Error(
            "%s is currently stopped, run faws ec2 start to start the instance"
            % instance["ID"]
        )
    elif instance["Status"] != "running":
        raise EC2Error(
            "%s is still in %s state, please wait"
            % (instance["ID"], instance["Status"])
        )


def get_instance_ip(instance: dict, ip_type: str = "dns") -> Optional[str]:
    """get instance ip

    :param instance: instance detail
    :type instance: dict
    :param ip_type: what ip to get
    :type ip_type: str, optional
    :return: selected instance ip address or dns address
    :rtype: str
    """
    if ip_type == "dns":
        if instance.get("PublicDnsName") and instance["PublicDnsName"] != " ":
            return instance["PublicDnsName"]
        else:
            ip_type = "public"
    if ip_type == "public":
        if instance.get("PublicIpAddress") and instance["PublicIpAddress"] != " ":
            return instance["PublicDnsName"]
        else:
            ip_type = "private"
    if ip_type == "private":
        if instance.get("PrivateIpAddress") and instance["PrivateIpAddress"] != " ":
            return instance["PrivateIpAddress"]
        raise EC2Error(
            "%s doesn't have an available ip associated, instance is likely not running"
        )


def ssh_instance(
    profile: Union[str, bool] = False,
    region: Union[str, bool] = False,
    bastion: bool = False,
    username: str = "ec2-user",
    tunnel: Union[bool, str] = False,
) -> None:
    """function to handle ssh operation intot the ec2 instance

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
    ssh_key_location = os.path.expanduser(
        os.getenv("FZFAWS_EC2_KEYPAIRS", default="~/.ssh")
    )
    os.chdir(ssh_key_location)
    ssh_key = "%s/%s.pem" % (ssh_key_location, ec2.instance_list[0]["KeyName"])

    if not tunnel:
        print("Instance is running, ready to connect")
        # check for file existence
        if os.path.isfile(ssh_key):
            cmd_list = ["ssh"]
            if bastion:
                cmd_list.append("-A")
            # if for custom VPC doesn't have public dns name, use public ip address
            cmd_list.extend(
                [
                    "-i",
                    ssh_key,
                    "%s@%s" % (username, get_instance_ip(ec2.instance_list[0])),
                ]
            )
        else:
            raise EC2Error("Key pair not detected in the specified directory")

    else:
        print("Jumpbox instance is running")
        if type(tunnel) == str:
            destination_username = tunnel
        else:
            destination_username = username
        ec2.set_ec2_instance(
            multi_select=False, header="select the destination instance"
        )

        check_instance_status(ec2.instance_list[1])
        print("Instance is running, ready to connect")

        destination_ssh_key = "%s/%s.pem" % (
            ssh_key_location,
            ec2.instance_list[1]["KeyName"],
        )
        if os.path.isfile(ssh_key) and os.path.isfile(destination_ssh_key):
            cmd_list = [
                "ssh",
                "-A",
                "-i",
                ssh_key,
                "%s@%s" % (username, get_instance_ip(ec2.instance_list[0])),
                "-t",
                "ssh",
                "%s@%s" % (destination_username, get_instance_ip(ec2.instance_list[1])),
            ]
        else:
            raise EC2Error("Key pair not detected in the specified directory")

    ssh = subprocess.Popen(cmd_list, shell=False)
    # allow user input
    stdoutdata, stderrdata = ssh.communicate()
    if stdoutdata:
        print(stdoutdata)
    if stderrdata:
        print(stderrdata)
