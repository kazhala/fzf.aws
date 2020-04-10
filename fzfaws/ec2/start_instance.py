"""start the selected instance/instances

Contains the main function for starting ec2 instances
"""
import json
from fzfaws.utils.util import get_confirmation
from fzfaws.ec2.ec2 import EC2


def start_instance(profile=False, region=False, wait=False, check=False):
    """start the selected instance

    Args:
        profile: string or bool, use a different profile for this operation
        region: string or bool, use a different region for this operation
        wait: bool, pause the function and wait for instance to be started before ending the function
        check: bool, pause the function and wait for 2/2 status checks of the instance
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
    if get_confirmation('Above instance will be started, continue?'):
        print('Starting instance now..')
        response = ec2.client.start_instances(
            InstanceIds=ec2.instance_ids,
        )
        response.pop('ResponseMetadata', None)
        print(json.dumps(response, indent=4, default=str))
        print(80*'-')
        print('Instance start initiated')

        if check:
            print('Wating for instance to be running and 2/2 status checked..')
            ec2.wait('instance_status_ok')
            print('Instance is ready')
        elif wait:
            print('Wating for instance to be running...')
            ec2.wait('instance_running')
            print('Instance is running')
