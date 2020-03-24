"""cloudformation drift detections

detect drift status of the selected cloudformations stack
"""
import json
import time
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.cform.cform import Cloudformation


def drift_stack(args):
    """perform actions on stack drift

    Args:
        args: argparser args
        cloudformation: instance of the Cloudformation class
    Returns:
        None
    Raises:
        NoSelectionMade: when the required selection received empty result
    """

    cloudformation = Cloudformation()
    cloudformation.set_stack()

    print(json.dumps(
        cloudformation.stack_details['DriftInformation'], indent=4, default=str))
    print(80*'-')

    response = cloudformation.client.describe_stack_resources(
        StackName=cloudformation.stack_name,
    )
    response_list = response['StackResources']

    if args.info:
        response = cloudformation.client.describe_stack_resource_drifts(
            StackName=cloudformation.stack_name,
        )
        response.pop('ResponseMetadata', None)
        print(json.dumps(response, indent=4, default=str))
    elif not args.select:
        response = cloudformation.client.detect_stack_drift(
            StackName=cloudformation.stack_name
        )
        drift_id = response['StackDriftDetectionId']
        wait_drift_result(cloudformation, drift_id)

    else:
        # prepare fzf
        for resource in response_list:
            resource['Drift'] = resource['DriftInformation']['StackResourceDriftStatus']
        fzf = Pyfzf()
        fzf.process_list(response['StackResources'],
                         'LogicalResourceId', 'ResourceType', 'Drift', gap=4)
        logical_id_list = fzf.execute_fzf(multi_select=True)

        if len(logical_id_list) < 1:
            print('No resources selected')
            exit()
        elif len(logical_id_list) == 1:
            # get individual resource drift status
            response = cloudformation.client.detect_stack_resource_drift(
                StackName=cloudformation.stack_name,
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
            response = cloudformation.client.detect_stack_drift(
                StackName=cloudformation.stack_name,
                LogicalResourceIds=logical_id_list
            )
            drift_id = response['StackDriftDetectionId']
            wait_drift_result(cloudformation, drift_id)


def wait_drift_result(cloudformation, drift_id):
    """Wait for the drift detection result

    aws doesn't provide wait condition, thus creating my own

    Args:
        cloudformation: instance of the Cloudformation class
        drift_id: string, drift detection id from the boto3 response
    Returns:
        None
    """
    print('Drift detection initiated')
    print(f"DriftDetectionId: {drift_id}")
    print('Wating for drift detection to complete..')

    while True:
        time.sleep(5)
        response = cloudformation.client.describe_stack_drift_detection_status(
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
