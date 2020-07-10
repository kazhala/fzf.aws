"""Module contains the wrapper class to interacte with route53."""
import re
from typing import Any, Dict, List, Optional, Union

from fzfaws.utils import BaseSession, Pyfzf, Spinner


class Route53(BaseSession):
    """The wrapper class for route53.

    Inherite from BaseSession to better control profile, region.

    At the moment is still just a helper class to other
    class like Cloudformation.

    :param profile: profile to use for this operation
    :type profile: Union[bool, str], optional
    :param region: region to use for this operation
    :type region: Union[bool, str], optional
    """

    def __init__(
        self,
        profile: Optional[Union[str, bool]] = None,
        region: Optional[Union[str, bool]] = None,
    ) -> None:
        """Construct route53 class."""
        super().__init__(profile=profile, region=region, service_name="route53")
        self.zone_ids: list = [""]

    def set_zone_id(
        self,
        zone_ids: Optional[Union[str, List[str]]] = None,
        multi_select: bool = False,
    ) -> None:
        """Set the hostedzone id for futher operations.

        :param zone_ids: list of zone_ids to set
        :type zone_ids: list, optional
        :param multi_select: allow multi_select
        :type multi_select: bool, optional
        """
        if zone_ids is None:
            fzf = Pyfzf()
            with Spinner.spin(message="Fetching hostedzones ..."):
                paginator = self.client.get_paginator("list_hosted_zones")
                for result in paginator.paginate():
                    result = self._process_hosted_zone(result["HostedZones"])
                    fzf.process_list(result, "Id", "Name")
            zone_ids = fzf.execute_fzf(multi_select=multi_select, empty_allow=True)
        if type(zone_ids) == str:
            self.zone_ids[0] = str(zone_ids)
        elif type(zone_ids) == list:
            self.zone_ids = list(zone_ids)

    def _process_hosted_zone(
        self, hostedzone_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process hostedzone as the response is not raw id.

        boto3 response for some reason doesn't return the actual zone, but rather
        with some prefex, this helper function just use a regex to get the actual
        id.

        :param hostedzone_list: The raw response from boto3
        :type hostedzone_list: List[Dict[str, Any]]
        :return: the formatted list of dictionary with correct hostedzone id.
        :rtype: List[Dict[str, Any]]
        """
        id_list: list = []
        id_pattern = r"/hostedzone/(?P<id>.*)$"
        for hosted_zone in hostedzone_list:
            raw_zone_id = re.search(id_pattern, hosted_zone["Id"]).group("id")
            id_list.append({"Id": raw_zone_id, "Name": hosted_zone.get("Name")})
        return id_list
