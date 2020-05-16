"""kms class for interacting with kms service

Handle selection of kms keys
"""
from fzfaws.utils import Pyfzf, BaseSession
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
    ):
        """set the key for kms using fzf"""
        if not keyids:
            fzf = Pyfzf()
            paginator = self.client.get_paginator("list_aliases")
            for result in paginator.paginate():
                aliases = [
                    alias for alias in result.get("Aliases") if alias.get("TargetKeyId")
                ]
                fzf.process_list(aliases, "TargetKeyId", "AliasName", "AliasArn")
            keyids = fzf.execute_fzf(
                header=header, multi_select=multi_select, empty_allow=empty_allow
            )
        if type(keyids) == str:
            self.keyids[0] = str(keyids)
        elif type(keyids) == list:
            self.keyids = list(keyids)
