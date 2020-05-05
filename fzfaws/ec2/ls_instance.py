"""ls instance to show basic information

list instance and describe instance
"""
import json
from fzfaws.ec2.ec2 import EC2


def ls_instance(profile=False, region=False):
    """display information about the instance

    :param profile: profile to use for this operation
    :type profile: Union[bool, str], optional
    :param region: region to use for this operation
    :type region: Union[bool, str], optional
    """

    ec2 = EC2(profile, region)
    ec2.set_ec2_instance()
    response = ec2.client.describe_instances(InstanceIds=ec2.instance_ids)
    response.pop("ResponseMetadata", None)
    print(json.dumps(response, indent=4, default=str))
