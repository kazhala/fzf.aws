"""ls instance to show basic information

list instance and describe instance
"""
import json
from fzfaws.ec2.ec2 import EC2


def ls_instance(profile=False, region=False):
    """display information about the instance
    Args:
        profile: stirng or bool, use a different profile for this operation
        region: string or bool, use a different region for this operation
    Exceptions:
        ClientError: boto3 client error
        NoSelectionMade: when required fzf selection did not get a selection
    """

    ec2 = EC2(profile, region)
    ec2.set_ec2_instance()
    response = ec2.client.describe_instances(
        InstanceIds=ec2.instance_ids
    )
    response.pop('ResponseMetadata', None)
    print(json.dumps(response, indent=4, default=str))
