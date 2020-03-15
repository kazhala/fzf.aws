"""ssh into the instance

perform ssh operation
"""
import os
import subprocess
from fzfaws.ec2.ec2 import EC2
home = os.path.expanduser('~')


def ssh_instance(args):
    """function to handle ssh operation intot the ec2 instance

    connect to ec2 instance through subprocess calling ssh
    May use other package later, but for now, is sufficient enough

    Args:
        args: argparse args
    Returns:
        None
    """
    ec2 = EC2()

    if args.region:
        ec2.get_ec2_region()
    ec2.get_ec2_instance(muti_select=False)

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
            if args.bastion:
                ssh = subprocess.Popen(
                    ['ssh', '-A', '-i', ssh_key, '%s@%s' %
                        (args.user[0], ec2.instance['PublicDnsName'])],
                    shell=False,
                )
            else:
                ssh = subprocess.Popen(
                    ['ssh', '-i', ssh_key, '%s@%s' %
                        (args.user[0], ec2.instance['PublicDnsName'])],
                    shell=False,
                )
            stdoutdata, stderrdata = ssh.communicate()
            if stdoutdata:
                print(stdoutdata)
        else:
            print('Key pair not detected in the specified directory')

    else:
        print('Instance is still in %s state, please wait' %
              ec2.instance['Status'])
