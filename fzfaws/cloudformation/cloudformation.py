"""Cloudformation class to interact with boto3 cloudformation client

Main reason to create a class is to handle different account profile usage
and different region, so that all initialization of boto3.client could happen
in a centralized place
"""
import boto3
import sys
from fzfaws.utils.session import BaseSession
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.util import search_dict_in_list
from fzfaws.utils.spinner import Spinner


class Cloudformation(BaseSession):
    """Cloudformation class to interact with boto3.client('cloudformaiton')

    handles operations directly related to boto3.client

    Attributes:
        client: boto3 client
        stack_name: then name of the selected stack
        stack_details: a dict containing response from boto3
    """

    def __init__(self, profile=None, region=None):
        super().__init__(profile=profile, region=region, service_name='cloudformation')
        self.stack_name = None
        self.stack_details = None

    def set_stack(self):
        """stores the selected stack into the instance"""
        fzf = Pyfzf()
        stack_list = []
        paginator = self.client.get_paginator('describe_stacks')
        for result in paginator.paginate():
            stack_list.extend(result['Stacks'])
            fzf.process_list(result['Stacks'], 'StackName',
                             'StackStatus', 'Description')
        self.stack_name = fzf.execute_fzf(empty_allow=False)
        self.stack_details = search_dict_in_list(
            self.stack_name, stack_list, 'StackName')

    def get_stack_resources(self):
        """list all stack logical resources

        return the selected list of logical resources
        """
        fzf = Pyfzf()
        paginator = self.client.get_paginator('list_stack_resources')
        for result in paginator.paginate(StackName=self.stack_name):
            fzf.process_list(
                result.get('StackResourceSummaries'), 'LogicalResourceId', 'ResourceType', 'PhysicalResourceId')
        return fzf.execute_fzf(multi_select=True)

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
                WaiterConfig={
                    'Delay': delay,
                    'MaxAttempts': attempts
                },
                **kwargs
            )
            spinner.stop()
            # join back the thread to main thread
            spinner.join()
        except (KeyboardInterrupt, SystemExit):
            spinner.stop()
            spinner.join()
            print('Exit')
            sys.exit()

    def execute_with_capabilities(self, capabilities=False, cloudformation_action=None, **kwargs):
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
            if not capabilities:
                response = cloudformation_action(**kwargs)
            else:
                response = cloudformation_action(
                    **kwargs, Capabilities=self._get_capabilities())
        except self.client.exceptions.InsufficientCapabilitiesException as e:
            response = cloudformation_action(
                **kwargs, Capabilities=self._get_capabilities())
        return response

    def _get_capabilities(self):
        """display help message and let user select capabilities"""
        fzf = Pyfzf()
        fzf.append_fzf('CAPABILITY_IAM\n')
        fzf.append_fzf('CAPABILITY_NAMED_IAM\n')
        fzf.append_fzf('CAPABILITY_AUTO_EXPAND')
        print(80*'-')
        print('Some of the resources in your template require capabilities')
        print('Template macros, nested stacks and iam roles/policies would require explicit acknowledgement')
        print('More information: https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html')
        print('Please select the capabilities to acknowledge and proceed (press tab to multi select)')
        return fzf.execute_fzf(empty_allow=True, print_col=1, multi_select=True)
