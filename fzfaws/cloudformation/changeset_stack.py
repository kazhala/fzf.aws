"""changeset related actions of stacks

create/view changeset of the cloudformation stacks
"""
import json
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.cloudformation.update_stack import update_stack
from fzfaws.utils.exceptions import NoNameEntered
from fzfaws.cloudformation.cloudformation import Cloudformation
from fzfaws.utils.util import get_confirmation


def describe_changes(cloudformation, changeset_name):
    """get the result of the changeset

    Args:
        stack_name: string, name of the stack
        changeset_name: string, name of the changeset
    Returns:
        None
    """

    response = cloudformation.client.describe_change_set(
        ChangeSetName=changeset_name,
        StackName=cloudformation.stack_name,
    )
    print('StackName: %s' % (cloudformation.stack_name))
    print('ChangeSetName: %s' % (changeset_name))
    print('Changes:')
    print(json.dumps(response['Changes'], indent=4, default=str))


def changeset_stack(profile=False, region=False, replace=False, tagging=False, local_path=False, root=False, capabilities=False, wait=False, info=False, execute=False, extra=False):
    """handle changeset actions

    Args:
        profile: string or bool, use a different profile for this operation
        region: string or bool, use a different region for this operation
        replace: bool, create changeset with replace template option
        tagging: bool, set tags for new changeset
        local_path: string or bool, use local template rather than s3
        root: bool, search from root
        capabilities: bool, execute with capabilities
        wait: bool, pause the function and wait for changeset create complete
        info: bool, display result of a changeset
        execute: bool, execute the selected changeset
        extra: bool, configure extra settings during chagset creation
            E.g. iam, sns, rolback etc configuration
    Returns:
        None
    Raises:
        NoNameEntered: when the new changeset receive empty string for new name
    """

    cloudformation = Cloudformation(profile, region)
    cloudformation.set_stack()

    # if not creating new changeset
    if info or execute:
        fzf = Pyfzf()
        response = cloudformation.client.list_change_sets(
            StackName=cloudformation.stack_name
        )
        response_list = response['Summaries']
        # get the changeset name
        fzf.process_list(response_list, 'ChangeSetName', 'StackName',
                         'ExecutionStatus', 'Status', 'Description')
        selected_changeset = fzf.execute_fzf()

        if info:
            describe_changes(cloudformation, selected_changeset)

        # execute the change set
        elif execute:
            if get_confirmation('Execute changeset %s?' % selected_changeset):
                response = cloudformation.client.execute_change_set(
                    ChangeSetName=selected_changeset,
                    StackName=cloudformation.stack_name
                )
                cloudformation.wait('stack_update_complete',
                                    'Wating for stack to be updated..')
                print('Stack updated')

    else:
        changeset_name = input('Enter name of this changeset: ')
        if not changeset_name:
            raise NoNameEntered('No changeset name specified')
        changeset_description = input('Description: ')
        # since is almost same operation as update stack
        # let update_stack handle it, but return update details instead of execute
        cloudformation_args = update_stack(
            cloudformation.profile, cloudformation.region, replace, tagging, local_path, root, capabilities, wait, dryrun=True, extra=extra, cloudformation=cloudformation)
        cloudformation_args['cloudformation_action'] = cloudformation.client.create_change_set
        cloudformation_args.update({
            'ChangeSetName': changeset_name,
            'Description': changeset_description
        })

        response = cloudformation.execute_with_capabilities(
            **cloudformation_args)

        response.pop('ResponseMetadata', None)
        print(json.dumps(response, indent=4, default=str))
        print(80*'-')
        print('Changeset create initiated')

        if wait:
            cloudformation.wait('change_set_create_complete',
                                'Wating for changset to be created..', ChangeSetName=changeset_name)
            print('Changeset created')
            describe_changes(cloudformation, changeset_name)
