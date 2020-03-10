# drift detection on the stack/resources
import boto3
import json
from pyfaws.pyfzf import PyFzf

cloudformation = boto3.client('cloudformation')


def drift_stack(args, stack_name):
    response = cloudformation.describe_stack_resources(
        StackName=stack_name,
    )
    response_list = response['StackResources']
    for resource in response_list:
        resource['Drift'] = resource['DriftInformation']['StackResourceDriftStatus']
    fzf = PyFzf()
    logical_id_list = fzf.process_list(response['StackResources'],
                                       'LogicalResourceId', 'ResourceType', 'Drift', multi_select=True, gap=4)

    if len(logical_id_list) < 1:
        print('No resources selected, to check the entire stack drift status, add -a flag')
        exit()
    elif len(logical_id_list) == 1:
        response = cloudformation.detect_stack_resource_drift(
            StackName=stack_name,
            LogicalResourceId=logical_id_list[0]
        )
        print(json.dumps(response['StackResourceDrift'],
                         indent=4, sort_keys=True, default=str))
        print(80*'-')
        print(
            f"LogicalResourceId: {response['StackResourceDrift']['LogicalResourceId']}")
        print(
            f"StackResourceDriftStatus: {response['StackResourceDrift']['StackResourceDriftStatus']}")
