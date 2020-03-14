# create/view changeset of the cloudformations stakcs
import boto3
import json
from pyfaws.pyfzf import PyFzf
from pyfaws.cform.update_stack import update_stack
from pyfaws.cform.helper.get_capabilities import cloudformation_with_capabilities

cloudformation = boto3.client('cloudformation')


def changeset_stack(args, stack_name, stack_details):
    if args.info or args.execute:
        fzf = PyFzf()
        response = cloudformation.list_change_sets(
            StackName=stack_name
        )
        response_list = response['Summaries']
        selected_changeset = fzf.process_list(response_list, 'ChangeSetName', 'StackName',
                                              'ExecutionStatus', 'Status', 'Description')
        if args.info:
            response = cloudformation.describe_change_set(
                ChangeSetName=selected_changeset,
                StackName=stack_name,
            )
            print('StackName: %s' % (stack_name))
            print('ChangeSetName: %s' % (selected_changeset))
            print('Changes:')
            print(json.dumps(response['Changes'], indent=4, default=str))
        elif args.execute:
            response = cloudformation.execute_change_set(
                ChangeSetName=selected_changeset,
                StackName=stack_name
            )
            print(response)

    else:
        changeset_name = input('Enter name of this changeset: ')
        if not changeset_name:
            raise Exception('No changeset name specified')
        changeset_description = input('Description: ')
        # since is almost same operation as update stack
        # let update_stack handle it, but return update details instead of execute
        update_details = update_stack(args, stack_name, stack_details)
        if not args.replace:
            response = cloudformation_with_capabilities(
                args=args,
                cloudformation_action=cloudformation.create_change_set,
                StackName=stack_name,
                UsePreviousTemplate=True,
                Parameters=update_details['Parameters'],
                Tags=update_details['Tags'],
                ChangeSetName=changeset_name,
                Description=changeset_description
            )
        else:
            if args.local:
                response = cloudformation_with_capabilities(
                    args=args,
                    cloudformation_action=cloudformation.create_change_set,
                    StackName=stack_name,
                    TemplateBody=update_details['TemplateBody'],
                    UsePreviousTemplate=False,
                    Parameters=update_details['Parameters'],
                    Tags=update_details['Tags'],
                    ChangeSetName=changeset_name,
                    Description=changeset_description
                )
            else:
                response = cloudformation_with_capabilities(
                    args=args,
                    cloudformation_action=cloudformation.create_change_set,
                    StackName=stack_name,
                    TemplateURL=update_details['TemplateURL'],
                    UsePreviousTemplate=False,
                    Parameters=update_details['Parameters'],
                    Tags=update_details['Tags'],
                    ChangeSetName=changeset_name,
                    Description=changeset_description
                )

        print(response)

