"""Contains function to terminate the instance."""
import json
from typing import Union

from fzfaws.ec2 import EC2
from fzfaws.utils import get_confirmation


def terminate_instance(
    profile: Union[str, bool] = False,
    region: Union[str, bool] = False,
    wait: bool = False,
) -> None:
    """Terminate the instance.

    :param profile: profile to use for this operation
    :type profile: Union[bool, str]
    :param region: region to use for this operation
    :type region: Union[bool, str]
    :param wait: wait for instance to be terminated
    :type wait: bool, optional
    """
    ec2 = EC2(profile, region)
    ec2.set_ec2_instance()

    ec2.print_instance_details()
    if get_confirmation("Above instance will be terminated, continue?"):
        print("Terminating instance now")
        response = ec2.client.terminate_instances(InstanceIds=ec2.instance_ids)
        response.pop("ResponseMetadata", None)
        print(json.dumps(response, indent=4, default=str))
        print(80 * "-")
        print("Instance termination initiated")

        if wait:
            ec2.wait("instance_terminated", "Wating for instance to be terminated..")
            print("Instance terminated")
