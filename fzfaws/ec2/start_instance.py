"""start the selected instance/instances

Contains the main function for starting ec2 instances
"""
import json
from fzfaws.utils.util import get_confirmation
from fzfaws.ec2.ec2 import EC2


def start_instance(args):
    """start the selected instance

    Args:
        args: argparse args
    Returns:
        None
    """
    ec2 = EC2()

    if args.region:
        ec2.get_ec2_region()
    ec2.get_ec2_instance()

    instance_ids = ec2.get_ec2_ids()
    if get_confirmation('Above instance/instances will be started, continue?'):
        print('Starting instance now..')
        response = ec2.client.start_instances(
            InstanceIds=instance_ids,
        )
        response.pop('ResponseMetadata', None)
        print(json.dumps(response, indent=4, default=str))
