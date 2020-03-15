"""ec2 wrapper class

A simple wrapper class of ec2 to interact with boto3.client('ec2')
"""
import boto3
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.util import get_name_tag, search_dict_in_list


class EC2:
    """ec2 wrapper class

    handles operation for all ec2 related task with boto3.client('ec2')

    Attributes:
        client: boto3 client
        instane: dict, the selected instance from boto3 response
    """

    def __init__(self, region=None, profile=None):
        """region is limited due to ec2 not avalilable in all region"""
        # TODO: handle cloudformation invalid regions
        self.client = boto3.client('ec2')
        self.instance = None
        self.instance_list = []
        self.instance_ids = []

    def set_ec2_region(self):
        """get ec2 supported region

        list region and use fzf to store region in the instance
        """
        response = self.client.describe_regions(
            AllRegions=True
        )
        fzf = Pyfzf()
        region = fzf.process_list(
            response['Regions'], 'RegionName', empty_allow=False)
        self.client = boto3.client('ec2', region_name=region)

    def set_ec2_instance(self, multi_select=True):
        """list all ec2 in the current selected region

        store the selected instance details in the instance attribute
        """
        response = self.client.describe_instances()
        fzf = Pyfzf()
        response_list = []
        # prepare the list for fzf
        for instance in response['Reservations']:
            response_list.append({
                'InstanceId': instance['Instances'][0]['InstanceId'],
                'InstanceType': instance['Instances'][0]['InstanceType'],
                'Status': instance['Instances'][0]['State']['Name'],
                'Name': get_name_tag(instance['Instances'][0]),
                'KeyName': instance['Instances'][0]['KeyName'] if 'KeyName' in instance['Instances'][0] else 'N/A',
                'PublicDnsName': instance['Instances'][0]['PublicDnsName'] if instance['Instances'][0]['PublicDnsName'] else 'N/A',
                'PublicIpAddress': instance['Instances'][0]['PublicIpAddress'] if 'PublicIpAddress' in instance['Instances'][0] else 'N/A'
            })
        selected_instance_ids = fzf.process_list(
            response_list, 'InstanceId', 'Status', 'InstanceType', 'Name', 'KeyName', 'PublicDnsName', 'PublicIpAddress', empty_allow=False, multi_select=multi_select)
        if multi_select:
            self.instance_ids = selected_instance_ids
            for instance in self.instance_ids:
                self.instance_list.append(search_dict_in_list(
                    instance, response_list, 'InstanceId'))
        else:
            self.instance = search_dict_in_list(
                selected_instance_ids, response_list, 'InstanceId')

    def print_instance_details(self):
        """display information of selected instances

        call this method before calling boto3 to do any ec2 opeartion
        and get confirmation
        """
        for instance in self.instance_list:
            print('InstanceId: %s  Name: %s' %
                  (instance['InstanceId'], instance['Name']))

    def wait(self, waiter_name, delay=15, attempts=40):
        """wait for the operation to be completed

        Args:
            waiter_name: string, name from boto3 waiter
            delay: number, how long between each attempt
            attempts: number, max attempts, usually 60mins, so 30 * 120
        Returns:
            None
            will pause the program until finish or error raised
        """
        waiter = self.client.get_waiter(waiter_name)
        waiter.wait(
            InstanceIds=self.instance_ids,
            WaiterConfig={
                'Delay': delay,
                'MaxAttempts': attempts
            },
        )
