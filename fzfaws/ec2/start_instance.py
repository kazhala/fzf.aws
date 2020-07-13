"""Contains the start_instance function."""
import json
from typing import Union

from fzfaws.ec2 import EC2
from fzfaws.utils import get_confirmation


def start_instance(
    profile: Union[str, bool] = False,
    region: Union[str, bool] = False,
    wait: bool = False,
    check: bool = False,
) -> None:
    """Start the selected instance.

    :param profile: profile to use for this operation
    :type profile: Union[bool, str], optional
    :param region: region to use for this operation
    :type region: Union[bool, str], optional
    :param wait: wait for instance start
    :type wait: bool, optional
    :param check: wait for all checks to be finished
    :type check: bool, optional
    """
    ec2 = EC2(profile, region)
    ec2.set_ec2_instance()

    ec2.print_instance_details()
    if get_confirmation("Above instance will be started, continue?"):
        print("Starting instance now ...")
        response = ec2.client.start_instances(InstanceIds=ec2.instance_ids,)
        response.pop("ResponseMetadata", None)
        print(json.dumps(response, indent=4, default=str))
        print(80 * "-")
        print("Instance start initiated")

        if check:
            print("Wating for instance to be running and 2/2 status checked ...")
            ec2.wait("instance_status_ok")
            print("Instance is ready")
        elif wait:
            ec2.wait("instance_running", "Wating for instance to be running ...")
            print("Instance is running")
