# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2024 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This module contains the class to connect to the CheckpointApproval contract."""

from typing import Dict
from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from aea_ledger_ethereum import EthereumApi


PUBLIC_ID = PublicId.from_str("valory/checkpoint_approval:0.1.0")


class CheckpointApproval(Contract):
    """The CheckpointApproval contract."""

    contract_id = PUBLIC_ID

    @classmethod
    def get_approval_status(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        checkpoint_id: int,
        party: str
    ) -> Dict[str, bool]:
        """Get the approval status for a specific party for a given checkpoint."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        if party == "seller":
            approved = contract_instance.functions.isSellerApproved(checkpoint_id).call()
        elif party == "buyer":
            approved = contract_instance.functions.isBuyerApproved(checkpoint_id).call()
        elif party == "platform":
            approved = contract_instance.functions.isPlatformApproved(checkpoint_id).call()
        elif party == "transporter":
            approved = contract_instance.functions.isTransporterApproved(checkpoint_id).call()
        else:
            raise ValueError(f"Unknown party: {party}. Must be one of: seller, buyer, platform, transporter.")

        return dict(approved=approved)

    @classmethod
    def get_approvers(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        checkpoint_id: int
    ) -> Dict[str, str]:
        """Get the approvers for a given checkpoint."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        approvers = contract_instance.functions.checkpointApprovers(checkpoint_id).call()
        return dict(
            seller=approvers[0],
            buyer=approvers[1],
            platform=approvers[2],
            transporter=approvers[3]
        )

    @classmethod
    def get_approval_data(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        checkpoint_id: int
    ) -> Dict[str, Dict[str, bool]]:
        """Get both the approval status and approvers for a given checkpoint."""
        approval_status = cls.get_approval_status(ledger_api, contract_address, checkpoint_id)
        approvers = cls.get_approvers(ledger_api, contract_address, checkpoint_id)

        return {
            "approval_status": approval_status,
            "approvers": approvers,
        }
