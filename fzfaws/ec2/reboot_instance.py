"""reboot the selected instance/instances

contains main function for rebooting instance
"""
from fzfaws.ec2.ec2 import EC2
from fzfaws.utils.util import get_confirmation


def reboot_instance(profile=False, region=False):
    """reboot the selected instances

    Args:
        profile: string or bool, use a different profile for this operation
        region: string or bool, use a different region for this operation
    Returns:
        None
    Exceptions:
        ClientError: boto3 client error
        NoSelectionMade: when required fzf selection did not get a selection
        subprocess.CalledProcessError: when local file search did not get a file
    """

    ec2 = EC2(region, profile)
    ec2.set_ec2_instance()

    ec2.print_instance_details()
    if get_confirmation('Above instance will be rebooted, continue?'):
        response = ec2.client.reboot_instances(
            InstanceIds=ec2.instance_ids
        )
        print(80*'-')
        print('Instance in being placed in the reboot queue')
        print('It may take aws up to 4mins before it is rebooted')
        print('Instance will remain in running state')
