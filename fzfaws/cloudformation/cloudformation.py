"""Cloudformation class to interact with boto3 cloudformation client

Main reason to create a class is to handle different account profile usage
and different region, so that all initialization of boto3.client could happen
in a centralized place
"""
from fzfaws.utils.util import search_dict_in_list
import json
import os
import re
from typing import Any, Generator, List, Dict

from fzfaws.utils import (
    Pyfzf,
    BaseSession,
    Spinner,
    get_confirmation,
)


class Cloudformation(BaseSession):
    """Cloudformation class to interact with boto3.client('cloudformation')

    handles operations directly related to boto3.client, but nothing else.
    Stuff like process template args or handling cloudformation settings,
    use the cloudformationargs class in helper.

    :param profile: use a different profile for this operation
    :type profile: Union[str, bool], optional
    :param region: use a different region for this operation
    :type region: Union[str, bool], optional
    """

    def __init__(self, profile=None, region=None):
        super().__init__(profile=profile, region=region, service_name="cloudformation")
        self.stack_name: str = ""
        self.stack_details: dict = {}

    def set_stack(self) -> None:
        """stores the selected stack into the instance attribute
        """

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

    def get_stack_resources(self, empty_allow: bool = False) -> List[str]:
        """list all stack logical resources

        :param empty_allow: allow empty selection
        :type empty_allow: bool, optional
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
        return list(fzf.execute_fzf(multi_select=True, empty_allow=empty_allow))

    def wait(self, waiter_name, message=None, delay=15, attempts=240, **kwargs):
        """wait for the operation to be completed

        Args:
            waiter_name: string, name from boto3 waiter
            message: string, loading message
            delay: number, how long between each attempt
            attempts: number, max attempts, usually 60mins, so 30 * 120
            **kwargs: rest of args for specific waiters like changeset waiter require ChangeSetName
        Returns:
            None
            will pause the program until finish or error raised
        Exceptions:
            KeyboardInterrupt: when user ctrl-c stop the program
            SystemExit: on system attempting to quit
                The above exceptions are handled and correctly stop all threads
        """
        try:
            spinner = Spinner(message=message)
            # spinner is a child thread
            spinner.start()
            waiter = self.client.get_waiter(waiter_name)
            waiter.wait(
                StackName=self.stack_name,
                WaiterConfig={"Delay": delay, "MaxAttempts": attempts},
                **kwargs
            )
            spinner.stop()
        except:
            Spinner.clear_spinner()
            raise

    def execute_with_capabilities(self, cloudformation_action=None, **kwargs):
        """execute the cloudformation_action with capabilities handled

        Args:
            capabilities: bool, execute with capabilities
            cloudformation_action: function, the cloudformation method to execute
            **kwargs: key ward args to use in the cloudformation_action
            example:
                instance.execute_with_capabilities(args, instance.client.update_stack, StackName=stack_name)
        Returns:
            the raw response from boto3
        Raises:
           InsufficientCapabilitiesException: when the stack action require extra acknowledgement
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

    def _get_capabilities(self, message=""):
        """display help message and let user select capabilities

        Args:
            message: string, capability error message to display
        """
        fzf = Pyfzf()
        fzf.append_fzf("CAPABILITY_IAM\n")
        fzf.append_fzf("CAPABILITY_NAMED_IAM\n")
        fzf.append_fzf("CAPABILITY_AUTO_EXPAND")
        message += "\nPlease select the capabilities to acknowledge and proceed"
        message += "\nMore information: https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html"
        return fzf.execute_fzf(
            empty_allow=True, print_col=1, multi_select=True, header=message
        )
