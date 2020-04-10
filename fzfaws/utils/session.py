"""base session class for all fzfaws aws wrapper classes

Wraps around boto3 session for better profile region management
"""
from boto3.session import Session
from fzfaws.utils.pyfzf import Pyfzf


class BaseSession:
    """base session class for managing profile and regions

    wraps around boto3 session and should be used for inheritence

    Attributes:
        session: boto3 session with customized profile and regions
        client: boto3 client init from the session
        resource: boto3 resource init from the session
    """

    def __init__(self, profile=None, region=None, service_name=None):
        """construtor of BaseSession class

        Args:
            profile: string or bool, if string, skip fzf and set profile
                if bool, set profile through fzf, if None, skip use default profile
            regions: string or bool, if string, skip fzf and set region
                if bool, set region through fzf, if None, skip use default region
            service_name: the service name for boto to init
        """
        session = Session()
        selected_profile = None
        selected_region = None
        if profile and type(profile) == bool:
            fzf = Pyfzf()
            for profile in session.available_profiles:
                fzf.append_fzf('%s\n' % profile)
            selected_profile = fzf.execute_fzf(empty_allow=True, print_col=1)
        elif profile and type(profile) == str:
            selected_profile = profile

        if region and type(region) == bool:
            fzf = Pyfzf()
            regions = session.get_available_regions(service_name)
            for region in regions:
                fzf.append_fzf('%s\n' % region)
            selected_region = fzf.execute_fzf(empty_allow=True, print_col=1)
        elif region and type(region) == str:
            selected_region = region
        self.session = Session(region_name=selected_region,
                               profile_name=selected_profile)
        self.client = self.session.client(service_name)
        self.resource = self.session.resource(service_name)
