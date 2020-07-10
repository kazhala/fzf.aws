"""Module contains the kms class for interacting with kms."""
from typing import Optional, Union

from fzfaws.utils import BaseSession, Pyfzf, Spinner


class KMS(BaseSession):
    """The kms wrapper class to handle operation around kms.

    Inherite from BaseSession to better control profile, region.

    At the moment is still just a helper class to other
    class like Cloudformation.

    :param profile: profile to use for this operation
    :type profile: Union[str, bool], optional
    :param region: region to use for this operation
    :type region: Union[str, bool], optional
    """

    def __init__(
        self,
        profile: Optional[Union[str, bool]] = None,
        region: Optional[Union[str, bool]] = None,
    ) -> None:
        """Construct the kms instane."""
        super().__init__(profile=profile, region=region, service_name="kms")
        self.keyids: list = [""]

    def set_keyids(
        self,
        keyids: Optional[Union[list, str]] = None,
        header: Optional[str] = None,
        multi_select: bool = False,
        empty_allow: bool = True,
    ) -> None:
        """Set the key for kms for further operations.

        :param keyids: keyids to set
        :type keyids: Union[list, str], optional
        :param header: header information in fzf
        :type header: str, optional
        :param multi_select: enable multi select
        :type multi_select: bool, optional
        :param empty_allow: allow empty selection
        :type empty_allow: bool, optional
        """
        if not keyids:
            fzf = Pyfzf()
            with Spinner.spin(message="Fetching kms keys ..."):
                paginator = self.client.get_paginator("list_aliases")
                for result in paginator.paginate():
                    aliases = [
                        alias
                        for alias in result.get("Aliases")
                        if alias.get("TargetKeyId")
                    ]
                    fzf.process_list(aliases, "TargetKeyId", "AliasName", "AliasArn")
            keyids = fzf.execute_fzf(
                header=header, multi_select=multi_select, empty_allow=empty_allow
            )
        if type(keyids) == str:
            self.keyids[0] = str(keyids)
        elif type(keyids) == list:
            self.keyids = list(keyids)
