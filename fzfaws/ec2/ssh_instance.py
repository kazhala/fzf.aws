"""ssh into the instance

perform ssh operation
"""
import os
import subprocess
from fzfaws.ec2.ec2 import EC2
from fzfaws.utils.exceptions import EC2Error

home = os.path.expanduser("~")


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

    if ec2.instance_list[0]["Status"] == "stopped":
        raise EC2Error(
            "Instance is currently stopped, run faws ec2 start to start the instance"
        )

    elif ec2.instance_list[0]["Status"] == "running":
        print("Instance is running, ready to connect")
        ssh_key_location = os.getenv("FAWS_KEY_LOCATION", default="%s/.ssh" % (home))
        os.chdir(ssh_key_location)
        ssh_key = "%s/%s.pem" % (ssh_key_location, ec2.instance_list[0]["KeyName"])
        if not tunnel:
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
                ssh = subprocess.Popen(cmd_list, shell=False,)
                # allow user input
                stdoutdata, stderrdata = ssh.communicate()
                if stderrdata or stdoutdata:
                    if stdoutdata:
                        print(stdoutdata)
                    if stderrdata:
                        print(stderrdata)
            else:
                raise EC2Error("Key pair not detected in the specified directory")

        else:
            if type(tunnel) == str:
                destination_username = tunnel
            else:
                destination_username = username
            ec2.set_ec2_instance(
                multi_select=False, header="select the destination instance"
            )
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
                ssh = subprocess.Popen(cmd_list, shell=False)
                # allow user input
                stdoutdata, stderrdata = ssh.communicate()
                if stderrdata or stdoutdata:
                    if stdoutdata:
                        print(stdoutdata)
                    if stderrdata:
                        print(stderrdata)

            else:
                raise EC2Error("Key pair not detected in the specified directory")

    else:
        raise EC2Error(
            "Instance is still in %s state, please wait"
            % ec2.instance_list[0]["Status"]
        )
