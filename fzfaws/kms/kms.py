"""kms class for interacting with kms service

Handle selection of kms keys
"""
from fzfaws.utils import Pyfzf, BaseSession, Spinner
from typing import Union, Optional


class KMS(BaseSession):
    """kms wrapper class around boto3.client('kms')

    handles operation around kms, selection/creation etc

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
        super().__init__(profile=profile, region=region, service_name="kms")
        self.keyids: list = [""]

    def set_keyids(
        self,
        keyids: Optional[Union[list, str]] = None,
        header: Optional[str] = None,
        multi_select: bool = False,
        empty_allow: bool = True,
    ) -> None:
        """set the key for kms using fzf

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
