"""wrapper class for route53

Wraps around boto3.client('route53') and supports region and profile
"""
from fzfaws.utils.session import BaseSession


class Route53(BaseSession):
    """wrapper class for route53

    Handles all operation related to route53

    Attributes:
        client: object, boto3.client('route53'), init from BaseSession
        resource: object, boto3.resource('route53'), init from BaseSession
        profile: string, current profile using for this session
        region: string, current region using for this session
    """

    def __init__(self, profile=None, region=None):
        """

        Args:
            profile: string or bool, use different profile for current operation
            region: string or bool, use different region for current operation
        """
        super().__init__(profile=profile, region=region, service_name='route53')
