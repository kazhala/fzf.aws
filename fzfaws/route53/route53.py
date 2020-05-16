"""wrapper class for route53

Wraps around boto3.client('route53') and supports region and profile
"""
import re
from fzfaws.utils import BaseSession, Pyfzf, Spinner
from typing import Union, Optional


class Route53(BaseSession):
    """wrapper class for route53

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
        """construct route53 class
        """
        super().__init__(profile=profile, region=region, service_name="route53")
        self.zone_ids: list = [""]

    def set_zone_id(
        self, zone_ids: Optional[Union[str, list]] = None, multi_select: bool = False
    ) -> None:
        """set the hostedzone

        :param zone_ids: list of zone_ids to set
        :type zone_ids: list, optional
        :param multi_select: allow multi_select
        :type multi_select: bool, optional
        """
        try:
            if zone_ids is None:
                fzf = Pyfzf()
                spinner = Spinner(message="Fetching hostedzones..")
                spinner.start()
                for result in self.get_paginated_result("list_hosted_zones"):
                    result = self._process_hosted_zone(result["HostedZones"])
                    fzf.process_list(result, "Id", "Name")
                spinner.stop()
                zone_ids = fzf.execute_fzf(multi_select=multi_select, empty_allow=True)
            if type(zone_ids) == str:
                self.zone_ids[0] = str(zone_ids)
            elif type(zone_ids) == list:
                self.zone_ids = list(zone_ids)
        except:
            Spinner.clear_spinner()
            raise

    def _process_hosted_zone(self, hostedzone_list: list) -> list:
        """process hostedzone as the response is not raw id
        """
        id_list: list = []
        id_pattern = r"/hostedzone/(?P<id>.*)$"
        for hosted_zone in hostedzone_list:
            raw_zone_id = re.search(id_pattern, hosted_zone["Id"]).group("id")
            id_list.append({"Id": raw_zone_id, "Name": hosted_zone.get("Name", "N/A")})
        return id_list
