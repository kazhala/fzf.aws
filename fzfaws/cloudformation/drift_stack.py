"""Contains function to handle drift detection."""
import json
import time
from typing import List, Union

from fzfaws.cloudformation import Cloudformation
from fzfaws.utils import Spinner


def drift_stack(
    profile: Union[str, bool] = False,
    region: Union[str, bool] = False,
    info: bool = False,
    select: bool = False,
    wait: bool = False,
) -> None:
    """Perform actions on stack drift.

    Info: print drift info.

    Select: select resource and detect its drift.

    Default: init and wait for the drift result of the entire stack.

    :param profile: use a different profile for the operation
    :type profile: Union[str, bool], optional
    :param region: use a different region for this operation
    :type region: Union[str, bool], optional
    :param info: display drift status instead of initiate a drift detection
    :type info: bool, optional
    :param select: select individual iresource and detect drift, otherwise, it will perform stack level check
    :type select: bool, optional
    :param wait: wait for the drfit detection
    :type wait: bool, optional
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
        drift_id: str = response["StackDriftDetectionId"]
        print("Drift detection initiated")
        print("DriftDetectionId: %s" % drift_id)
        if wait:
            wait_drift_result(cloudformation, drift_id)

    else:
        logical_id_list: List[str] = cloudformation.get_stack_resources()

        if len(logical_id_list) == 1:
            # get individual resource drift status
            response = cloudformation.client.detect_stack_resource_drift(
                StackName=cloudformation.stack_name,
                LogicalResourceId=logical_id_list[0],
            )
            print(json.dumps(response["StackResourceDrift"], indent=4, default=str))
            print(80 * "-")
            print(
                "LogicalResourceId: %s"
                % response["StackResourceDrift"]["LogicalResourceId"]
            )
            print(
                "StackResourceDriftStatus: %s"
                % response["StackResourceDrift"]["StackResourceDriftStatus"]
            )

        else:
            # get all selected resource status
            response = cloudformation.client.detect_stack_drift(
                StackName=cloudformation.stack_name, LogicalResourceIds=logical_id_list
            )
            drift_id: str = response["StackDriftDetectionId"]
            print("Drift detection initiated")
            print("DriftDetectionId: %s" % drift_id)
            if wait:
                wait_drift_result(cloudformation, drift_id)


def wait_drift_result(cloudformation: Cloudformation, drift_id: str) -> None:
    """Wait for the drift detection result.

    Since aws doesn't provide wait condition, creating a custom waiter.

    :param cloudformation: Cloudformation instance
    :type cloudformation: Cloudformation
    :param drift_id: the id of the drift detection
    :type drift_id: str
    """
    delay, max_attempts = cloudformation._get_waiter_config()
    attempts: int = 0
    response = None
    with Spinner.spin(message="Wating for drift detection to complete ..."):
        while attempts <= max_attempts:
            time.sleep(delay)
            response = cloudformation.client.describe_stack_drift_detection_status(
                StackDriftDetectionId=drift_id
            )
            if response.get("DetectionStatus") != "DETECTION_IN_PROGRESS":
                break
    if response is not None:
        response.pop("ResponseMetadata", None)
        print(json.dumps(response, indent=4, default=str))
        print(80 * "-")
        if response["DetectionStatus"] == "DETECTION_COMPLETE":
            print("StackDriftStatus: %s" % response.get("StackResourceDriftStatus"))
            print(
                "DriftedStackResourceCount: %s"
                % response.get("DriftedStackResourceCount")
            )
        else:
            print("Drift detection failed")
    else:
        print("Waiter failed: Max attempts exceeded")
