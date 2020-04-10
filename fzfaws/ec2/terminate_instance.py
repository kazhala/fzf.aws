"""terminate the selected instance

contains main function for terminating the instance
"""
import json
from fzfaws.ec2.ec2 import EC2
from fzfaws.utils.util import get_confirmation


def terminate_instance(profile=False, region=False, wait=False):
    """terminate the instance

    Args:
        profile: string or bool, use a different profile for this operation
        region: string or bool, use a different region for this operation
        wait: bool, pause the function and wait for instance to be terminated
    Returns:
        None
    Exceptions:
        ClientError: boto3 client error
        NoSelectionMade: when required fzf selection did not get a selection
    """

    ec2 = EC2(region, profile)
    ec2.set_ec2_instance()

    ec2.print_instance_details()
    if get_confirmation('Above instance will be terminated, continue?'):
        print('Terminating instance now')
        response = ec2.client.terminate_instances(
            InstanceIds=ec2.instance_ids
        )
        response.pop('ResponseMetadata', None)
        print(json.dumps(response, indent=4, default=str))
        print(80*'-')
        print('Instance termination initiated')

        if wait:
            print('Wating for instance to be terminated..')
            ec2.wait('instance_terminated')
            print('Instance terminated')
