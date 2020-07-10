"""The base session class for all fzfaws aws wrapper classes.

Wraps around boto3 session for better profile, region management,
all class responsible to interacte with boto3 should inherite
from the BaseSession class.
"""
import os
from typing import Optional, Union

from boto3.session import Session

from fzfaws.utils import Pyfzf


class BaseSession:
    """The base session class for managing profile and regions.

    This class sets the profile and region based on user cmd flags
    and config files. Inherite this class for any class require
    to interacte with boto3 to ensure the profile and region
    are set consistently.

    if profile or region is not set, the default value in awscli
    configureation will be used.

    :param profile: profile to use for next operation
    :type profile: Union[str, bool], optional
    :param region: region to use for next operation
    :type region: Union[str, bool], optional
    :param service_name: name of boto3 service to init
    :type service_name: str
    """

    def __init__(
        self,
        profile: Optional[Union[str, bool]] = None,
        region: Optional[Union[str, bool]] = None,
        service_name: str = "",
    ) -> None:
        """Construct a BaseSession instance.

        If profile or region is True value, then
        fzf will be launched to let user select region or profile.
        """
        session = Session()
        selected_profile: Optional[str] = None
        selected_region: Optional[str] = None
        if profile and type(profile) == bool:
            fzf = Pyfzf()
            for profile in session.available_profiles:
                fzf.append_fzf("%s\n" % profile)
            selected_profile = str(fzf.execute_fzf(print_col=1))
        elif profile and type(profile) is str:
            selected_profile = str(profile)

        if region and type(region) == bool:
            fzf = Pyfzf()
            regions = session.get_available_regions(service_name)
            for region in regions:
                fzf.append_fzf("%s\n" % region)
            selected_region = str(fzf.execute_fzf(print_col=1))
        elif region and type(region) is str:
            selected_region = str(region)

        if not selected_profile:
            selected_profile = os.getenv("FZFAWS_%s_PROFILE" % service_name.upper(), "")
            if not selected_profile:
                selected_profile = os.getenv("FZFAWS_GLOBAL_PROFILE", None)
        if not selected_region:
            selected_region = os.getenv("FZFAWS_%s_REGION" % service_name.upper(), "")
            if not selected_region:
                selected_region = os.getenv("FZFAWS_GLOBAL_REGION", None)

        self.profile: Optional[str] = selected_profile
        self.region: Optional[str] = selected_region
        self.session = Session(
            region_name=selected_region, profile_name=selected_profile
        )
        self._client = self.session.client(service_name)

        # only certain service support resource
        resources = self.session.get_available_resources()
        if service_name in resources:
            self._resource = self.session.resource(service_name)

    @property
    def client(self):
        """Return the client."""
        return self._client

    @property
    def resource(self):
        """Return the resource."""
        return self._resource
