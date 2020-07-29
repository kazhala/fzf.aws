"""Module contains functions to handle lambda invokations."""
import base64
import json
import pprint
from typing import Dict, Union

from fzfaws.lambdaf import Lambdaf
from fzfaws.utils import Spinner


def invoke_function(
    profile: Union[str, bool] = False,
    region: Union[str, bool] = False,
    asynk: bool = False,
    all_version: bool = False,
):
    """Invoke the selected lambda function.

    :param profile: use a different profile for this operation
    :type profile: Union[str, bool], optional
    :param region: use a different region for this operation
    :type region: Union[str, bool], optional
    :param asynk: invoke function asynchronously, asynk for no conflict with async
    :type asynk: bool, optional
    :param all_version: list all versions of lambda functions
    :type all_version: bool, optional
    """
    lambdaf = Lambdaf(profile, region)
    lambdaf.set_lambdaf(header="select function to invoke", all_version=all_version)
    if not asynk:
        invoke_function_sync(lambdaf)


def invoke_function_sync(lambdaf: Lambdaf) -> None:
    """Invoke the lambda synchronously.

    :param lambdaf: the instance of Lambdaf
    :type lambdaf: Lambdaf
    """
    function_args: Dict[str, str] = get_function_name(lambdaf.function_detail)
    function_args["InvocationType"] = "RequestResponse"

    with Spinner.spin(message="Invoking lambda function ..."):
        response = lambdaf.client.invoke(**function_args)
        response.pop("ResponseMetadata", None)
        response["Payload"] = json.loads(response["Payload"].read().decode("utf-8"))
        log_result = response.pop("LogResult", None)
        log_result = base64.b64decode(log_result).decode("utf-8")
    pprint.pprint(log_result)
    print(80 * "-")
    print(json.dumps(response, indent=4, default=str))


def get_function_name(details: Dict[str, str]) -> Dict[str, str]:
    """Get the argument for lambda invoke function.

    :param details: the selected lambda details
    :type details: Dict[str, str]
    """
    function_args: Dict[str, str] = {}
    if details.get("Version", "$LATEST") == "$LATEST":
        function_args["FunctionName"] = details["FunctionName"]
    else:
        function_args["FunctionName"] = "%s:%s" % (
            details["FunctionName"],
            details["Version"],
        )
    function_args["LogType"] = "Tail"
    return function_args
