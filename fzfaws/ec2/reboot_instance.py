"""reboot the selected instance/instances

contains main function for rebooting instance
"""
from fzfaws.ec2.ec2 import EC2
from fzfaws.utils.util import get_confirmation


def reboot_instance(args):
    """reboot the selected instances

    Args:
        args: subparser args
    Returns:
        None
    """

    ec2 = EC2()
    if args.region:
        ec2.set_ec2_region()
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
