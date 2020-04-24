"""contains wrapper class for cloudwatch

wrapps around boto3 client for centerilised management
"""
from fzfaws.utils.session import BaseSession
from fzfaws.utils.pyfzf import Pyfzf


class Cloudwatch(BaseSession):
    """cloudwatch wrapper class

    Handles all operation related to cloudwatch

    Attributes:
        client: boto3 client
        resource: boto3 resource
        region: region for the operation
        profile: profile used for the operation
        arns: selected arns
    """

    def __init__(self, profile=None, region=None):
        super().__init__(profile=profile, region=region, service_name='cloudwatch')
        self.arns = []

    def set_arns(self, arns=[], empty_allow=False, header=None, multi_select=False):
        """set cloudwatch arns for operation

        Args:
            arns: list, list of arns and skip fzf
            empty_allow: bool, if allow empty selection
            header: string, helper message to display in fzf header
            multi_select: bool, if multi_select is enabled
        """
        if not arns:
            fzf = Pyfzf()
            paginator = self.client.get_paginator('describe_alarms')
            for result in paginator.paginate():
                if result.get('CompositeAlarms'):
                    fzf.process_list(result['CompositeAlarms'], 'AlarmArn')
                if result.get('MetricAlarms'):
                    fzf.process_list(result['MetricAlarms'], 'AlarmArn')
            arns = fzf.execute_fzf(
                empty_allow=empty_allow, multi_select=multi_select, header=header)
            if not multi_select:
                arns = [arns]
        self.arns = arns
