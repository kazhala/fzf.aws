"""Module contains the cloudformation wrapper class."""
import json
import os
import re
from typing import Any, Callable, Dict, Generator, List, Tuple, Union

from fzfaws.utils import BaseSession, Pyfzf, Spinner, get_confirmation
from fzfaws.utils.util import search_dict_in_list


class Cloudformation(BaseSession):
    """Cloudformation wrapper class to interact with boto3.client('cloudformation').

    Handles operations directly related to boto3.client, but nothing else.
    Stuff like process template args or handling cloudformation settings,
    use the cloudformationargs class in helper.

    :param profile: use a different profile for this operation
    :type profile: Union[str, bool], optional
    :param region: use a different region for this operation
    :type region: Union[str, bool], optional
    """

    def __init__(
        self, profile: Union[str, bool] = None, region: Union[str, bool] = None
    ) -> None:
        """Construct the instance."""
        super().__init__(profile=profile, region=region, service_name="cloudformation")
        self.stack_name: str = ""
        self.stack_details: dict = {}

    def set_stack(self) -> None:
        """Store the selected stack into the instance attribute."""
        fzf = Pyfzf()
        with Spinner.spin(message="Fetching cloudformation stacks ..."):
            paginator = self.client.get_paginator("describe_stacks")
            response = paginator.paginate()
            stack_generator = self._get_stack_generator(response)
            for result in response:
                fzf.process_list(
                    result["Stacks"], "StackName", "StackStatus", "Description"
                )
        self.stack_name = str(fzf.execute_fzf(empty_allow=False))
        self.stack_details = search_dict_in_list(
            self.stack_name, stack_generator, "StackName"
        )

    def get_stack_resources(
        self, empty_allow: bool = False, header: str = None
    ) -> List[str]:
        """List all stack logical resources and return the selected resources.

        :param empty_allow: allow empty selection
        :type empty_allow: bool, optional
        :param header: information to be displayed in fzf header
        :type header: str, optional
        :return: selected list of logical resources LogicalResourceId
        :rtype: List[str]
        """
        fzf = Pyfzf()
        paginator = self.client.get_paginator("list_stack_resources")
        for result in paginator.paginate(StackName=self.stack_name):
            for resource in result.get("StackResourceSummaries"):
                resource["Drift"] = resource.get("DriftInformation").get(
                    "StackResourceDriftStatus"
                )
            fzf.process_list(
                result.get("StackResourceSummaries"),
                "LogicalResourceId",
                "ResourceType",
                "Drift",
            )
        return list(
            fzf.execute_fzf(multi_select=True, header=header, empty_allow=empty_allow)
        )

    def wait(self, waiter_name: str, message: str = None, **kwargs) -> None:
        """Wait for the operation to be completed.

        Require a waiter_name approved by boto3, because it's using boto3 waiter.

        :param waiter_name: name for the boto3 waiter
        :type waiter_name: str
        :param message: message to display for spinner
        :type message: str, optional
        """
        with Spinner.spin(message=message):
            waiter = self.client.get_waiter(waiter_name)
            delay, max_attempts = self._get_waiter_config()
            waiter.wait(
                StackName=self.stack_name,
                WaiterConfig={"Delay": delay, "MaxAttempts": max_attempts},
                **kwargs
            )

    def execute_with_capabilities(
        self, cloudformation_action: Callable[..., Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any]:
        """Execute the cloudformation_action with capabilities handled.

        When creating stacks with IAM role or nested stacks related, cloudformation
        require extra capabilities to be acknowledged before creating or updating the stack.
        This method will attempt to submit the request and handle the capabilities
        exceptions, then calling the _get_capabilities to get user acknowledge the capabilities.

        :param cloudformation_action: the function to execute for boto3
        :type cloudformation_action: Callable[..., Dict[str, Any]]
        :raises InsufficientCapabilitiesException: when the stack action require extra acknowledgement
        :return: boto3 response of the cloudformation action
        :rtype: Dict[str, Any]
        """
        try:
            print(json.dumps({**kwargs}, indent=4, default=str))
            if get_confirmation("Confirm?"):
                response = cloudformation_action(**kwargs)
            else:
                raise SystemExit
        except self.client.exceptions.InsufficientCapabilitiesException as e:
            pattern = r"^.*(Requires capabilities.*)$"
            error_msg = re.match(pattern, str(e)).group(1)
            response = cloudformation_action(
                **kwargs, Capabilities=self._get_capabilities(message=error_msg)
            )
        return response

    def _get_waiter_config(self) -> Tuple[int, int]:
        """Process env and return the waiter config.

        :return: return a tuple with delay and max_attempts
        :rtype: Tuple
        """
        waiter_config = os.getenv(
            "FZFAWS_CLOUDFORMATION_WAITER", os.getenv("FZFAWS_GLOBAL_WAITER", "")
        )
        delay: int = 30
        max_attempts: int = 120
        if waiter_config:
            waiter_config = json.loads(waiter_config)
            delay = int(waiter_config.get("delay", 30))
            max_attempts = int(waiter_config.get("max_attempts", 120))
        return (delay, max_attempts)

    def _get_capabilities(self, message: str = "") -> List[str]:
        """Display help message and let user select capabilities.

        :param message: message to display in fzf header
        :type message: str, optional
        :return: selected capabilities to acknowledge
        :rtype: List[str]
        """
        fzf = Pyfzf()
        fzf.append_fzf("CAPABILITY_IAM\n")
        fzf.append_fzf("CAPABILITY_NAMED_IAM\n")
        fzf.append_fzf("CAPABILITY_AUTO_EXPAND")
        message += "\nPlease select the capabilities to acknowledge and proceed"
        message += "\nMore information: https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html"
        return list(
            fzf.execute_fzf(
                empty_allow=True, print_col=1, multi_select=True, header=message
            )
        )

    def _get_stack_generator(
        self, response: List[Dict[str, Any]]
    ) -> Generator[Dict[str, Any], None, None]:
        """Create generator for boto3 paginator.

        Attempt to reduce unnecessary memory usage.

        :param response: response from paginator.paginate()
        :type response: List[Dict[str, Any]]
        """
        for result in response:
            for stack in result.get("Stacks", []):
                yield stack
