"""Stop the selected instances

contains main function for stopping the instance
"""
import json
from fzfaws.ec2.ec2 import EC2
from fzfaws.utils.util import get_confirmation


def stop_instance(profile=False, region=False, hibernate=False, wait=False):
    """stop the selected instance

    Args:
        profile: bool or string, use different profile for this operation
        region: bool or string, use different region for this operation
        hibernate: bool, stop instance hibernate, Note: instance doesn't support hibernate will raise error
        wait: bool, pause the function and wait for instance to be stopped
    Returns:
        None
    Exceptions:
        ClientError: boto3 client error
        NoSelectionMade: when required fzf selection did not get a selection
    """

    ec2 = EC2(region, profile)
    ec2.set_ec2_instance()

    ec2.print_instance_details()
    if get_confirmation('Above instance will be stopped, continue?'):
        print('Stopping instance now..')
        response = ec2.client.stop_instances(
            InstanceIds=ec2.instance_ids,
            Hibernate=hibernate
        )
        response.pop('ResponseMetadata', None)
        print(json.dumps(response, indent=4, default=str))
        print(80*'-')
        print('Instance stop initiated')

        if wait:
            print('Wating for instance to be stopped')
            ec2.wait('instance_stopped')
            print('Instance stopped')
