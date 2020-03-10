# drift detection on the stack/resources
import boto3
import json
import time
from pyfaws.pyfzf import PyFzf

cloudformation = boto3.client('cloudformation')


def drift_stack(args, stack_name, stack_details):
    print(json.dumps(
        stack_details['DriftInformation'], indent=4, default=str))
    print(80*'-')

    response = cloudformation.describe_stack_resources(
        StackName=stack_name,
    )
    response_list = response['StackResources']

    if args.info:
        response = cloudformation.describe_stack_resource_drifts(
            StackName=stack_name,
        )
        response.pop('ResponseMetadata', None)
        print(json.dumps(response, indent=4, default=str))
    elif not args.select:
        response = cloudformation.detect_stack_drift(
            StackName=stack_name
        )
        drift_id = response['StackDriftDetectionId']
        wait_drift_result(drift_id)

    else:
        # prepare fzf
        for resource in response_list:
            resource['Drift'] = resource['DriftInformation']['StackResourceDriftStatus']
        fzf = PyFzf()
        logical_id_list = fzf.process_list(response['StackResources'],
                                           'LogicalResourceId', 'ResourceType', 'Drift', multi_select=True, gap=4)

        if len(logical_id_list) < 1:
            print('No resources selected')
            exit()
        elif len(logical_id_list) == 1:
            # get individual resource drift status
            response = cloudformation.detect_stack_resource_drift(
                StackName=stack_name,
                LogicalResourceId=logical_id_list[0]
            )
            print(json.dumps(response['StackResourceDrift'],
                             indent=4, default=str))
            print(80*'-')
            print(
                f"LogicalResourceId: {response['StackResourceDrift']['LogicalResourceId']}")
            print(
                f"StackResourceDriftStatus: {response['StackResourceDrift']['StackResourceDriftStatus']}")

        else:
            # get all selected resource status
            response = cloudformation.detect_stack_drift(
                StackName=stack_name,
                LogicalResourceIds=logical_id_list
            )
            drift_id = response['StackDriftDetectionId']
            wait_drift_result(drift_id)


def wait_drift_result(drift_id):
    print('Drift detection initiated')
    print(f"DriftDetectionId: {drift_id}")
    print('Wating for drift detection to complete..')
    # aws doesn't provide wait condition for this, thus creating my own
    while True:
        time.sleep(5)
        response = cloudformation.describe_stack_drift_detection_status(
            StackDriftDetectionId=drift_id
        )
        if response['DetectionStatus'] != 'DETECTION_IN_PROGRESS':
            break
    response.pop('ResponseMetadata', None)
    print(json.dumps(response, indent=4, default=str))
    print(80*'-')
    if response['DetectionStatus'] == 'DETECTION_COMPLETE':
        print(f"StackDriftStatus: {response['StackDriftStatus']}")
        print(
            f"DriftedStackResourceCount: {response['DriftedStackResourceCount']}")
    else:
        print('Drift detection failed')
