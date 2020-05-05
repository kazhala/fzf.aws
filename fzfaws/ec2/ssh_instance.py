"""ssh into the instance

perform ssh operation
"""
import os
import subprocess
from fzfaws.ec2.ec2 import EC2

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
    """
    if type(tunnel) == str:
        username = tunnel
        tunnel = True

    ec2 = EC2(profile, region)
    ec2.set_ec2_instance(multi_select=False)

    if ec2.instance_list[0]["Status"] == "stopped":
        print("Instance is currently stopped, run faws ec2 start to start the instance")

    elif ec2.instance_list[0]["Status"] == "running":
        print("Instance is running, ready to connect")
        ssh_key_location = os.getenv("FAWS_KEY_LOCATION", default="%s/.ssh" % (home))
        os.chdir(ssh_key_location)
        ssh_key = "%s/%s.pem" % (ssh_key_location, ec2.instance_list[0]["KeyName"])
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
            print("Key pair not detected in the specified directory")

    else:
        print(
            "Instance is still in %s state, please wait"
            % ec2.instance_list[0]["Status"]
        )
