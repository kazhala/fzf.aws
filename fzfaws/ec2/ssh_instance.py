"""ssh into the instance

perform ssh operation
"""
import os
import subprocess
from fzfaws.ec2.ec2 import EC2
from fzfaws.utils.exceptions import EC2Error

home = os.path.expanduser("~")


def check_instance_status(instance):
    # type: (dict) -> None
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


def ssh_instance(
    profile=False, region=False, bastion=False, username="ec2-user", tunnel=False
):
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
    ssh_key_location = os.getenv("FAWS_KEY_LOCATION", default="%s/.ssh" % (home))
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
                    "%s@%s"
                    % (
                        username,
                        ec2.instance_list[0]["PublicDnsName"]
                        if ec2.instance_list[0]["PublicDnsName"] != "N/A"
                        else ec2.instance_list[0]["PublicIpAddress"],
                    ),
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
                "%s@%s"
                % (
                    username,
                    ec2.instance_list[0]["PublicDnsName"]
                    if ec2.instance_list[0]["PublicDnsName"] != "N/A"
                    else ec2.instance_list[0]["PublicIpAddress"],
                ),
                "-t",
                "ssh",
                "%s@%s"
                % (
                    destination_username,
                    ec2.instance_list[1]["PublicDnsName"]
                    if ec2.instance_list[1]["PublicDnsName"] != "N/A"
                    else ec2.instance_list[1]["PublicIpAddress"],
                ),
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
