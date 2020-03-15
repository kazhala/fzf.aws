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

    def get_ec2_region(self):
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

    def get_ec2_instance(self, muti_select=True):
        """list all ec2 in the current selected region

        store the selected instance details in the instance attribute
        """
        response = self.client.describe_instances()
        fzf = Pyfzf()
        response_list = []
        for instance in response['Reservations']:
            response_list.append({
                'InstanceId': instance['Instances'][0]['InstanceId'],
                'InstanceType': instance['Instances'][0]['InstanceType'],
                'Status': instance['Instances'][0]['State']['Name'],
                'Name': get_name_tag(instance['Instances'][0]),
                'KeyName': instance['Instances'][0]['KeyName'],
                'PublicDnsName': instance['Instances'][0]['PublicDnsName'] if instance['Instances'][0]['PublicDnsName'] else 'N/A'
            })
        selected_instance_id = fzf.process_list(
            response_list, 'InstanceId', 'Status', 'InstanceType', 'Name', 'KeyName', 'PublicDnsName', empty_allow=False, multi_select=muti_select)
        if muti_select:
            for instance in selected_instance_id:
                self.instance_list.append(search_dict_in_list(
                    instance, response_list, 'InstanceId'))
        self.instance = search_dict_in_list(
            selected_instance_id, response_list, 'InstanceId')
