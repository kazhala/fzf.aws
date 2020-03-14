# create/view changeset of the cloudformations stakcs
import boto3
import json
from pyfaws.pyfzf import PyFzf
from pyfaws.cform.update_stack import update_stack

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
            response.pop('ResponseMetadata', None)
            print(json.dumps(response, indent=4, default=str))
        elif args.execute:
            response = cloudformation.execute_change_set(
                ChangeSetName=selected_changeset,
                StackName=stack_name
            )
            print(response)
    else:
        update_details = update_stack(args, stack_name, stack_details)
        print(update_details)

