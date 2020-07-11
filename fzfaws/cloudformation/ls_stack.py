"""Contains the ls function to display information about the stack."""
import json
from typing import Union

from fzfaws.cloudformation.cloudformation import Cloudformation


def ls_stack(
    profile: Union[str, bool] = False,
    region: Union[str, bool] = False,
    resource: bool = False,
    name: bool = False,
    arn: bool = False,
    tag: bool = False,
    resource_type: bool = False,
) -> None:
    """Display stack/resource information.

    :param profile: use a different profile for this operation
    :type profile: Union[str, bool], optional
    :param region: use a different region for this operation
    :type region: Union[str, bool], optional
    :param resource: display resource information rather than stack information
    :type resource: bool, optional
    :param name: display name of stack or resource instead of the entire information 
    :type name: bool, optional
    :param arn: display arn of the stack instead of the entire stack information
    :type arn: bool, optional
    :param tag: display tag of the stack instead of the entire stack information
    :type tag: bool, optional
    :param resource_type: display type of the resource instead of the entire resource information
    :type resource_type: bool, optional
    """
    cloudformation = Cloudformation(profile, region)
    cloudformation.set_stack()

    if not resource:
        if not name and not arn and not tag:
            print(json.dumps(cloudformation.stack_details, indent=4, default=str))
        else:
            if name:
                print(cloudformation.stack_details["StackName"])
            if arn:
                print(cloudformation.stack_details["StackId"])
            if tag:
                print(cloudformation.stack_details.get("Tags", []))
    else:
        logical_id_list = cloudformation.get_stack_resources()
        for logical_id in logical_id_list:
            response = cloudformation.client.describe_stack_resource(
                StackName=cloudformation.stack_name, LogicalResourceId=logical_id
            )
            response.pop("ResponseMetadata", None)
            if not name and not resource_type:
                print(json.dumps(response, indent=4, default=str))
            else:
                if name:
                    print(response["StackResourceDetail"].get("LogicalResourceId"))
                if resource_type:
                    print(response["StackResourceDetail"].get("ResourceType"))
