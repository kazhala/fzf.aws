"""wrapper class for route53

Wraps around boto3.client('route53') and supports region and profile
"""
import re
from fzfaws.utils.session import BaseSession
from fzfaws.utils.pyfzf import Pyfzf


class Route53(BaseSession):
    """wrapper class for route53

    Handles all operation related to route53

    Attributes:
        client: object, boto3.client('route53'), init from BaseSession
        resource: object, boto3.resource('route53'), init from BaseSession
        profile: string, current profile using for this session
        region: string, current region using for this session
        zone_id: string, selected zone id
    """

    def __init__(self, profile=None, region=None, zone_id=None, zone_ids=None):
        """construct route53 class

        Args:
            profile: string or bool, use different profile for current operation
            region: string or bool, use different region for current operation
            zone_id: string, which hostedzone should action be perfomed
            zone_ids: list, list of zone id
        """
        super().__init__(profile=profile, region=region, service_name='route53')
        self.zone_id = zone_id
        self.zone_ids = zone_ids

    def set_zone_id(self, zone_id=None, zone_ids=None, multi_select=False):
        """set the hostedzone

        Args:
            zone_id: string
            zone_ids: list, list of zone ids
            multi_select: bool, set multiple zone_id
        """
        if zone_id:
            self.zone_id = zone_id
        elif zone_ids:
            self.zone_ids = zone_ids
        else:
            fzf = Pyfzf()
            paginator = self.client.get_paginator('list_hosted_zones')
            for result in paginator.paginate():
                result = self._process_hosted_zone(result['HostedZones'])
                fzf.process_list(result, 'Id', 'Name')
            if not multi_select:
                self.zone_id = fzf.execute_fzf(empty_allow=True)
            else:
                self.zone_ids = fzf.execute_fzf(
                    empty_allow=True, multi_select=multi_select)

    def _process_hosted_zone(self, hostedzone_list):
        """process hostedzone as the response is not raw id"""
        id_list = []
        id_pattern = r'/hostedzone/(?P<id>.*)$'
        for hosted_zone in hostedzone_list:
            raw_zone_id = re.search(
                id_pattern, hosted_zone['Id']).group('id')
            id_list.append(
                {'Id': raw_zone_id, 'Name': hosted_zone['Name']})
        return id_list
