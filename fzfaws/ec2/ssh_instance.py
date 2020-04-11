"""ssh into the instance

perform ssh operation
"""
import os
import subprocess
from fzfaws.ec2.ec2 import EC2
home = os.path.expanduser('~')


def ssh_instance(profile=False, region=False, bastion=False, username='ec2-user'):
    """function to handle ssh operation intot the ec2 instance

    connect to ec2 instance through subprocess calling ssh
    May use other package later, but for now, is sufficient enough

    Args:
        profile: string or bool, use a different profile for this operation
        region: string or bool, use a different region for this operation
        bastion: bool, whether to enable ssh forwarding
        username: string, default=ec2-user, username to ssh
    Returns:
        None
    Exceptions:
        ClientError: boto3 client error
        NoSelectionMade: when required fzf selection did not get a selection
    """

    ec2 = EC2(profile, region)
    ec2.set_ec2_instance(multi_select=False)

    if ec2.instance['Status'] == 'stopped':
        print('Instance is currently stopped, run faws ec2 start to start the instance')

    elif ec2.instance['Status'] == 'running':
        print('Instance is running, ready to connect')
        ssh_key_location = os.getenv(
            'FAWS_KEY_LOCATION', default='%s/.ssh' % (home))
        os.chdir(ssh_key_location)
        ssh_key = '%s/%s.pem' % (ssh_key_location, ec2.instance['KeyName'])
        # check for file existence
        if os.path.isfile(ssh_key):
            cmd_list = ['ssh']
            if bastion:
                cmd_list.append('-A')
            # if for custom VPC doesn't have public dns name, use public ip address
            cmd_list.extend(['-i', ssh_key, '%s@%s' % (username, ec2.instance['PublicDnsName']
                                                       if ec2.instance['PublicDnsName'] != 'N/A' else ec2.instance['PublicIpAddress'])])
            ssh = subprocess.Popen(
                cmd_list,
                shell=False,
            )
            # allow user input
            stdoutdata, stderrdata = ssh.communicate()
            if stderrdata or stdoutdata:
                if stdoutdata:
                    print(stdoutdata)
                if stderrdata:
                    print(stderrdata)
        else:
            print('Key pair not detected in the specified directory')

    else:
        print('Instance is still in %s state, please wait' %
              ec2.instance['Status'])
