"""Cloudformation class to interact with boto3 cloudformation client

Main reason to create a class is to handle different account profile usage
and different region, so that all initialization of boto3.client could happen
in a centralized place
"""
import boto3
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.util import search_dict_in_list


class Cloudformation:
    """Cloudformation class to interact with boto3.client('cloudformaiton')


    """

    def __init__(self, region=None, profile=None):
        self.client = boto3.client('cloudformation')
        self.stack_name = None
        self.stack_details = None

    def get_stack(self):
        response = self.client.describe_stacks()
        fzf = Pyfzf()
        self.stack_name = fzf.process_list(
            response['Stacks'], 'StackName', 'StackStatus', 'Description')
        self.stack_details = search_dict_in_list(
            self.stack_name, response['Stacks'], 'StackName')

    def wait(self, waiter_name, delay=15, attempts=240):
        waiter = self.client.get_waiter(waiter_name)
        print(80*'-')
        waiter.wait(
            StackName=self.stack_name,
            WaiterConfig={
                'Delay': delay,
                'MaxAttempts': attempts
            }
        )
