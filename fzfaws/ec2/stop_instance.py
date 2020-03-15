"""contains main function for stopping the instance

Stop the selected instances
"""
import json
from fzfaws.ec2.ec2 import EC2
from fzfaws.utils.util import get_confirmation


def stop_instance(args):
    """stop the selected instance

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
    if get_confirmation('Above instance will be stopped, continue?'):
        print('Stopping instance now..')
        response = ec2.client.stop_instances(
            InstanceIds=ec2.instance_ids,
            Hibernate=args.hibernate
        )
        response.pop('ResponseMetadata', None)
        print(json.dumps(response, indent=4, default=str))
        print(80*'-')
        print('Instance stop initiated')

        if args.wait:
            print('Wating for instance to be stopped')
            ec2.wait('instance_stopped')
            print('Instance stopped')
