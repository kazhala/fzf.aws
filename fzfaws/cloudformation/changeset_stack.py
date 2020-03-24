"""changeset related actions of stacks

create/view changeset of the cloudformation stacks
"""
import json
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.cloudformation.update_stack import update_stack
from fzfaws.utils.exceptions import NoNameEntered
from fzfaws.cloudformation.cloudformation import Cloudformation


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


def changeset_stack(args):
    """handle changeset actions

    Args:
        args: argparse args
    Returns:
        None
    Raises:
        NoNameEntered: when the new changeset receive empty string for new name
    """

    cloudformation = Cloudformation()
    cloudformation.set_stack()

    # if not creating new changeset
    if args.info or args.execute:
        fzf = Pyfzf()
        response = cloudformation.client.list_change_sets(
            StackName=cloudformation.stack_name
        )
        response_list = response['Summaries']
        # get the changeset name
        fzf.process_list(response_list, 'ChangeSetName', 'StackName',
                         'ExecutionStatus', 'Status', 'Description')
        selected_changeset = fzf.execute_fzf()

        if args.info:
            describe_changes(cloudformation, selected_changeset)

        # execute the change set
        elif args.execute:
            response = cloudformation.client.execute_change_set(
                ChangeSetName=selected_changeset,
                StackName=cloudformation.stack_name
            )
            print(response)

    else:
        changeset_name = input('Enter name of this changeset: ')
        if not changeset_name:
            raise NoNameEntered('No changeset name specified')
        changeset_description = input('Description: ')
        # since is almost same operation as update stack
        # let update_stack handle it, but return update details instead of execute
        update_details = update_stack(args, cloudformation)

        if not args.replace:
            response = cloudformation.execute_with_capabilities(
                args=args,
                cloudformation_action=cloudformation.client.create_change_set,
                StackName=cloudformation.stack_name,
                UsePreviousTemplate=True,
                Parameters=update_details['Parameters'],
                Tags=update_details['Tags'],
                ChangeSetName=changeset_name,
                Description=changeset_description
            )
        else:
            if args.local:
                response = cloudformation.execute_with_capabilities(
                    args=args,
                    cloudformation_action=cloudformation.client.create_change_set,
                    StackName=cloudformation.stack_name,
                    TemplateBody=update_details['TemplateBody'],
                    UsePreviousTemplate=False,
                    Parameters=update_details['Parameters'],
                    Tags=update_details['Tags'],
                    ChangeSetName=changeset_name,
                    Description=changeset_description
                )
            else:
                response = cloudformation.execute_with_capabilities(
                    args=args,
                    cloudformation_action=cloudformation.client.create_change_set,
                    StackName=cloudformation.stack_name,
                    TemplateURL=update_details['TemplateURL'],
                    UsePreviousTemplate=False,
                    Parameters=update_details['Parameters'],
                    Tags=update_details['Tags'],
                    ChangeSetName=changeset_name,
                    Description=changeset_description
                )

        response.pop('ResponseMetadata', None)
        print(json.dumps(response, indent=4, default=str))
        print(80*'-')
        print('Changeset create initiated')

        if args.wait:
            print('Wating for changset to be created..')
            cloudformation.wait('change_set_create_complete',
                                ChangeSetName=changeset_name)
            print('Changeset created')
            describe_changes(cloudformation, changeset_name)
