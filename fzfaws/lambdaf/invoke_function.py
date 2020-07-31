"""Module contains functions to handle lambda invokations."""
import base64
from fzfaws.utils.pyfzf import Pyfzf
import json
import pprint
from typing import Any, Dict, Union
from pathlib import Path

from fzfaws.lambdaf import Lambdaf
from fzfaws.utils import Spinner


def invoke_function(
    profile: Union[str, bool] = False,
    region: Union[str, bool] = False,
    asynk: bool = False,
    all_version: bool = False,
    payload: Union[str, bool] = False,
    root: bool = False,
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
    :param payload: a path to json file to provide lambda as input
    :type payload: Union[str, bool]
    :param root: search from home directory when payload = True
    :type root: bool, optional
    """
    lambdaf = Lambdaf(profile, region)
    lambdaf.set_lambdaf(header="select function to invoke", all_version=all_version)
    payload_path: str = ""
    if type(payload) == str:
        payload_path = str(payload)
    elif type(payload) == bool and payload == True:
        fzf = Pyfzf()
        payload_path = str(
            fzf.get_local_file(
                json=True,
                header="select a json file as payload",
                search_from_root=root,
            )
        )

    if not asynk:
        invoke_function_sync(lambdaf, payload_path)
    else:
        invoke_function_async(lambdaf, payload_path)


def invoke_function_async(lambdaf: Lambdaf, payload_path: str = "") -> None:
    """Invoke the lambda asynchronously.

    :param lambdaf: the instance of Lambdaf
    :type lambdaf: Lambdaf
    :param payload_path: path to lambda function payload
    :type payload_path: str, optional
    """
    function_args: Dict[str, Any] = get_function_args(
        lambdaf.function_detail, payload_path
    )
    function_args["InvocationType"] = "Event"
    response = lambdaf.client.invoke(**function_args)
    response.pop("ResponseMetadata", None)
    response.pop("ResponseMetadata", None)
    response.pop("Payload", None)
    print(json.dumps(response, indent=4, default=str))


def invoke_function_sync(lambdaf: Lambdaf, payload_path: str = "") -> None:
    """Invoke the lambda synchronously.

    :param lambdaf: the instance of Lambdaf
    :type lambdaf: Lambdaf
    :param payload_path: path to lambda function payload
    :type payload_path: str, optional
    """
    function_args: Dict[str, Any] = get_function_args(
        lambdaf.function_detail, payload_path
    )
    function_args["InvocationType"] = "RequestResponse"

    with Spinner.spin(message="Invoking lambda function ..."):
        response = lambdaf.client.invoke(**function_args)
        response.pop("ResponseMetadata", None)
        response["Payload"] = json.loads(response["Payload"].read().decode("utf-8"))
        log_result = response.pop("LogResult", None)
        log_result = base64.b64decode(log_result).decode("utf-8")
    pprint.pprint(log_result)
    print(json.dumps(response, indent=4, default=str))


def get_function_args(
    details: Dict[str, str], payload_path: str = ""
) -> Dict[str, Any]:
    """Get the argument for lambda invoke function.

    :param details: the selected lambda details
    :type details: Dict[str, str]
    :param payload_path: path to lambda function payload json file
    :type payload_path: str, optional
    """
    function_args: Dict[str, Any] = {}
    if details.get("Version", "$LATEST") == "$LATEST":
        function_args["FunctionName"] = details["FunctionName"]
    else:
        function_args["FunctionName"] = "%s:%s" % (
            details["FunctionName"],
            details["Version"],
        )
    function_args["LogType"] = "Tail"
    if payload_path:
        function_args["Payload"] = Path(payload_path).read_bytes()
    return function_args
