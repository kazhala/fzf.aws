"""Module contains changeset related actions of stacks."""
import json
from typing import Any, Dict, Union

from fzfaws.cloudformation import Cloudformation
from fzfaws.cloudformation.update_stack import update_stack
from fzfaws.utils import Pyfzf, get_confirmation
from fzfaws.utils.exceptions import NoNameEntered


def describe_changes(cloudformation: Cloudformation, changeset_name: str) -> None:
    """Get the result of the changeset.

    Only for printing information purpose.

    :param cloudformation: an instance of the Cloudformation class
    :type cloudformation: Cloudformation
    :param changeset_name: the name of the changeset
    :type changeset_name: str
    """
    response = cloudformation.client.describe_change_set(
        ChangeSetName=changeset_name, StackName=cloudformation.stack_name,
    )
    print("StackName: %s" % (cloudformation.stack_name))
    print("ChangeSetName: %s" % (changeset_name))
    print("Changes:")
    print(json.dumps(response["Changes"], indent=4, default=str))


def changeset_stack(
    profile: Union[str, bool] = False,
    region: Union[str, bool] = False,
    replace: bool = False,
    local_path: Union[str, bool] = False,
    root: bool = False,
    wait: bool = False,
    info: bool = False,
    execute: bool = False,
    delete: bool = False,
    extra: bool = False,
    bucket: str = None,
    version: Union[str, bool] = False,
) -> None:
    """Handle changeset actions.

    Main function to interacte with changeset, use argument
    to control the actions.

    This function is using update_stack to handle all the dirty
    works as both functions are processing cloudformation arguments
    and having the same arguments.

    :param profile: use a different profile for this operation
    :type profile: Union[bool, str], optional
    :param region: use a different region for this operation
    :type region: Union[bool, str], optional
    :param replace: replace the template during update
    :type replace: bool, optional
    :param local_path: Select a template from local machine
    :type local_path: Union[bool, str], optional
    :param root: Search local file from root directory
    :type root: bool, optional
    :param wait: wait for stack to be completed before exiting the program
    :type wait: bool, optional
    :param info: display result of a changeset
    :type info: bool, optional
    :param execute: execute changeset
    :type execute: bool, optional
    :param delete: delete changeset
    :type delete: bool, optional
    :param extra: configure extra options for the stack, (tags, IAM, termination protection etc..)
    :type extra: bool, optional
    :param bucket: specify a bucket/bucketpath to skip s3 selection
    :type bucket: str, optional
    :param version: use previous version of template in s3 bucket
    :type version: Union[bool, str], optional
    :raises NoNameEntered: If no changset name is entered
    """
    cloudformation = Cloudformation(profile, region)
    cloudformation.set_stack()

    # if not creating new changeset
    if info or execute or delete:
        fzf = Pyfzf()
        response: Dict[str, Any] = cloudformation.client.list_change_sets(
            StackName=cloudformation.stack_name
        )
        # get the changeset name
        fzf.process_list(
            response.get("Summaries", []),
            "ChangeSetName",
            "StackName",
            "ExecutionStatus",
            "Status",
            "Description",
        )

        if info:
            selected_changeset = str(fzf.execute_fzf())
            describe_changes(cloudformation, selected_changeset)

        # execute the change set
        elif execute:
            selected_changeset = fzf.execute_fzf()
            if get_confirmation("Execute changeset %s?" % selected_changeset):
                response = cloudformation.client.execute_change_set(
                    ChangeSetName=selected_changeset,
                    StackName=cloudformation.stack_name,
                )
                cloudformation.wait(
                    "stack_update_complete", "Wating for stack to be updated ..."
                )
                print("Stack updated")

        elif delete:
            selected_changeset = fzf.execute_fzf(multi_select=True)
            for changeset in selected_changeset:
                print("(dryrun) Delete changeset %s" % changeset)
            if get_confirmation("Confirm?"):
                for changeset in selected_changeset:
                    cloudformation.client.delete_change_set(
                        ChangeSetName=changeset, StackName=cloudformation.stack_name
                    )

    else:
        changeset_name = input("Enter name of this changeset: ")
        if not changeset_name:
            raise NoNameEntered("No changeset name specified")
        changeset_description = input("Description: ")
        # since is almost same operation as update stack
        # let update_stack handle it, but return update details instead of execute
        cloudformation_args = update_stack(
            cloudformation.profile,
            cloudformation.region,
            replace,
            local_path,
            root,
            wait,
            extra,
            bucket,
            version,
            dryrun=True,
            cloudformation=cloudformation,
        )
        cloudformation_args[
            "cloudformation_action"
        ] = cloudformation.client.create_change_set
        cloudformation_args["ChangeSetName"] = changeset_name
        if changeset_description:
            cloudformation_args["Description"] = changeset_description

        response = cloudformation.execute_with_capabilities(**cloudformation_args)

        response.pop("ResponseMetadata", None)
        print(json.dumps(response, indent=4, default=str))
        print(80 * "-")
        print("Changeset create initiated")

        if wait:
            cloudformation.wait(
                "change_set_create_complete",
                "Wating for changset to be created ...",
                ChangeSetName=changeset_name,
            )
            print("Changeset created")
            describe_changes(cloudformation, changeset_name)
