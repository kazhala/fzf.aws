"""Module contains the cloudformation function to delete stack."""
from typing import Any, Dict, List, Union

from fzfaws.cloudformation import Cloudformation
from fzfaws.iam import IAM
from fzfaws.utils import get_confirmation


def delete_stack(
    profile: Union[str, bool] = False,
    region: Union[str, bool] = False,
    wait: bool = False,
    iam: Union[str, bool] = False,
) -> None:
    """Handle deletion of the stack.

    Two situation, normal deletion and retained deletion.
    When the selected stack is already in a 'DELETE_FAILED' state, extra
    fzf operation would be triggered for user to select logical id to retain
    in order for deletion to be success.

    :param profile: use a different profile for this operation
    :type profile: Union[str, bool], optional
    :param region: use a different region for this operation
    :type region: Union[str, bool], optional
    :param wait: pause the function and wait for stack delete complete
    :type wait: bool, optional
    :param iam: specify a iam arn to delete this stack
    :type iam: Union[str, bool]
    :raises SystemExit: when user denied confirmation to delete stack, exit system
    """
    cloudformation = Cloudformation(profile, region)
    cloudformation.set_stack()

    logical_id_list: List[str] = []
    if cloudformation.stack_details["StackStatus"] == "DELETE_FAILED":
        header: str = "The stack is in the failed state, specify any resource to skip during deletion"
        logical_id_list = cloudformation.get_stack_resources(
            empty_allow=True, header=header
        )

    cloudformation_args: Dict[str, Any] = {"StackName": cloudformation.stack_name}
    if logical_id_list:
        cloudformation_args["RetainResources"] = logical_id_list

    if iam and type(iam) == str:
        cloudformation_args["RoleARN"] = iam
    elif iam and type(iam) == bool:
        iam_instance = IAM(profile=cloudformation.profile)
        iam_instance.set_arns(
            header="Select a iam role with permissions to delete the current stack",
            service="cloudformation.amazonaws.com",
        )
        if iam_instance.arns[0]:
            cloudformation_args["RoleARN"] = iam_instance.arns[0]

    if not get_confirmation(
        "Are you sure you want to delete the stack '%s'?" % cloudformation.stack_name
    ):
        raise SystemExit

    cloudformation.client.delete_stack(**cloudformation_args)
    print("Stack deletion initiated")

    if wait:
        cloudformation.wait(
            "stack_delete_complete", "Wating for stack to be deleted ..."
        )
        print("Stack deleted")
