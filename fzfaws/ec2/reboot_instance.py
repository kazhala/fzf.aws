"""This module contains the reboot function."""
from typing import Union

from fzfaws.ec2 import EC2
from fzfaws.utils import get_confirmation


def reboot_instance(
    profile: Union[str, bool] = False, region: Union[str, bool] = False
) -> None:
    """Reboot the selected instances.

    :param profile: profile to use for this operation
    :type profile: Union[bool, str], optional
    :param region: region to use for this operation
    :type region: Union[bool, str], optional
    """
    ec2 = EC2(profile, region)
    ec2.set_ec2_instance()

    ec2.print_instance_details()
    if get_confirmation("Above instance will be rebooted, continue?"):
        ec2.client.reboot_instances(InstanceIds=ec2.instance_ids)
        print(80 * "-")
        print("Instance in being placed in the reboot queue")
        print("It may take aws up to 4mins before it is rebooted")
        print("Instance will remain in running state")
