"""cloudformation drift detections

detect drift status of the selected cloudformations stack
"""
import json
import time
from fzfaws.cloudformation.cloudformation import Cloudformation
from fzfaws.utils.spinner import Spinner


def drift_stack(profile=False, region=False, info=False, select=False):
    """perform actions on stack drift

    Args:
        profile: string or bool, use a different profile for this operation
        region: string or bool, use a different region for this operation
        info: bool, display drift status instead of initiate a drift detection
        select: bool, select individual resource and detect, othewise, it will perform stack level check
    Returns:
        None
    Raises:
        NoSelectionMade: when the required selection received empty result
        ClientError: boto3 client error
    """

    cloudformation = Cloudformation(profile, region)
    cloudformation.set_stack()

    print(
        json.dumps(
            cloudformation.stack_details["DriftInformation"], indent=4, default=str
        )
    )
    print(80 * "-")

    if info:
        response = cloudformation.client.describe_stack_resource_drifts(
            StackName=cloudformation.stack_name,
        )
        response.pop("ResponseMetadata", None)
        print(json.dumps(response, indent=4, default=str))
    elif not select:
        response = cloudformation.client.detect_stack_drift(
            StackName=cloudformation.stack_name
        )
        drift_id = response["StackDriftDetectionId"]
        wait_drift_result(cloudformation, drift_id)

    else:
        logical_id_list = cloudformation.get_stack_resources()

        if len(logical_id_list) == 1:
            # get individual resource drift status
            response = cloudformation.client.detect_stack_resource_drift(
                StackName=cloudformation.stack_name,
                LogicalResourceId=logical_id_list[0],
            )
            print(json.dumps(response["StackResourceDrift"], indent=4, default=str))
            print(80 * "-")
            print(
                f"LogicalResourceId: {response['StackResourceDrift']['LogicalResourceId']}"
            )
            print(
                f"StackResourceDriftStatus: {response['StackResourceDrift']['StackResourceDriftStatus']}"
            )

        else:
            # get all selected resource status
            response = cloudformation.client.detect_stack_drift(
                StackName=cloudformation.stack_name, LogicalResourceIds=logical_id_list
            )
            drift_id = response["StackDriftDetectionId"]
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
    print("Drift detection initiated")
    print(f"DriftDetectionId: {drift_id}")
    spinner = Spinner(message="Wating for drift detection to complete..")

    spinner.start()
    while True:
        time.sleep(5)
        response = cloudformation.client.describe_stack_drift_detection_status(
            StackDriftDetectionId=drift_id
        )
        if response["DetectionStatus"] != "DETECTION_IN_PROGRESS":
            break
    spinner.stop()
    spinner.join()
    response.pop("ResponseMetadata", None)
    print(json.dumps(response, indent=4, default=str))
    print(80 * "-")
    if response["DetectionStatus"] == "DETECTION_COMPLETE":
        print(f"StackDriftStatus: {response['StackDriftStatus']}")
        print(f"DriftedStackResourceCount: {response['DriftedStackResourceCount']}")
    else:
        print("Drift detection failed")
