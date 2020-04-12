"""display informaiton of the stack

Can display stack resources as well
"""
import json
from fzfaws.cloudformation.cloudformation import Cloudformation


def ls_stack(profile=False, region=False, resource=False):
    """display stack information

    set resource to true to display information about stack
    resources.

    Args:
        profile: string or bool, use a different profile for this operation
        region: string or bool, use a different region for this operation
        resource: bool, whether to display information about resource
    Returns:
        None
    Exceptions:
        EmptyList: when there is no stack in the selected region
    """

    cloudformation = Cloudformation(profile, region)
    cloudformation.set_stack()

    if not resource:
        print(json.dumps(cloudformation.stack_details, indent=4, default=str))
    else:
        logical_id_list = cloudformation.get_stack_resources()
        for logical_id in logical_id_list:
            response = cloudformation.client.describe_stack_resource(
                StackName=cloudformation.stack_name,
                LogicalResourceId=logical_id
            )
            response.pop('ResponseMetadata', None)
            print(json.dumps(response, indent=4, default=str))
