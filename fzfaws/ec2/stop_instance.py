"""Stop the selected instances

contains main function for stopping the instance
"""
import json
from fzfaws.ec2.ec2 import EC2
from fzfaws.utils.util import get_confirmation


def stop_instance(profile=False, region=False, hibernate=False, wait=False):
    """stop the selected instance


    :param profile: profile to use for this operation
    :type profile: Union[bool, str], optional
    :param region: region to use for this operation
    :type region: Union[bool, str], optional
    :param hibernate: stop hibernate if instance support hibernate
    :type hibernate: bool, optional
    :param wait: wait for instance to be stopped
    :type wait: bool, optional
    """

    ec2 = EC2(profile, region)
    ec2.set_ec2_instance()

    ec2.print_instance_details()
    if get_confirmation("Above instance will be stopped, continue?"):
        print("Stopping instance now..")
        response = ec2.client.stop_instances(
            InstanceIds=ec2.instance_ids, Hibernate=hibernate
        )
        response.pop("ResponseMetadata", None)
        print(json.dumps(response, indent=4, default=str))
        print(80 * "-")
        print("Instance stop initiated")

        if wait:
            ec2.wait("instance_stopped", "Wating for instance to be stopped")
            print("Instance stopped")
