# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2024 Valory AG
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

"""This package contains round behaviours of LearningAbciApp."""

from abc import ABC
import json
import random
from typing import Generator, Set, Type, cast

from aea_ledger_cosmos import AEAEnforceError

from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.contracts.erc20.contract import ERC20
from packages.valory.protocols.ledger_api import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import AbstractRound
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.learning_abci.models import CoinData, Params, SharedState
from packages.valory.skills.learning_abci.payloads import (
    APICheckPayload,
    DecisionMakingPayload,
    TxPreparationPayload,
)
from packages.valory.skills.learning_abci.rounds import (
    APICheckRound,
    DecisionMakingRound,
    Event,
    LearningAbciApp,
    SynchronizedData,
    TxPreparationRound,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import hash_payload_to_hex


HTTP_OK = 200
GNOSIS_CHAIN_ID = "gnosis"
TX_DATA = b"0x"
SAFE_GAS = 0
VALUE_KEY = "value"
TO_ADDRESS_KEY = "to_address"


class LearningBaseBehaviour(BaseBehaviour, ABC):  # pylint: disable=too-many-ancestors
    """Base behaviour for the learning_abci skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, super().params)

    @property
    def local_state(self) -> SharedState:
        """Return the state."""
        return cast(SharedState, self.context.state)


class APICheckBehaviour(LearningBaseBehaviour):  # pylint: disable=too-many-ancestors
    """APICheckBehaviour"""

    matching_round: Type[AbstractRound] = APICheckRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            sender = self.context.agent_address
            price = yield from self.get_price()
            balance = yield from self.get_balance()
            payload = APICheckPayload(sender=sender, price=price, balance=balance)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def get_price(self):
        """Get token price from Coingecko"""
        # Interact with Coingecko's API
        coingecko_api_key = self.params.coingecko_api_key
        coingecko_url = self.params.coingecko_price_template.replace("{api_key}", coingecko_api_key)
        
        result = yield from self.get_http_response(
            url=coingecko_url,
            method="GET",
        )
        data: CoinData = json.loads(result.body)
        price = data["autonolas"]["usd"]
        self.context.logger.info(f"Price is {price}")
        return price

    def get_balance(self):
        """Get balance"""
        # Use the contract api to interact with the ERC20 contract
        # result = yield from self.get_contract_api_response()
        self.context.logger.info(f"Getting balance from ledger...")
        self.context.logger.info(f"Safe contract address is {self.synchronized_data.safe_contract_address}")

        wxdai_contract_address=self.params.wxdai_contract_address
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION, # type: ignore
            contract_address=wxdai_contract_address,
            account=self.synchronized_data.safe_contract_address,
            contract_id=str(ERC20.contract_id),
            contract_callable="check_balance",
            chain_id=GNOSIS_CHAIN_ID,
        )
        self.context.logger.info(f"response: {contract_api_response}")
        try:
            balance = contract_api_response.raw_transaction.body.get('token')
        except (AEAEnforceError, KeyError, ValueError, TypeError):
            balance = None
        self.context.logger.info(f"Balance is {balance}")
        return balance


class DecisionMakingBehaviour(
    LearningBaseBehaviour
):  # pylint: disable=too-many-ancestors
    """DecisionMakingBehaviour"""

    matching_round: Type[AbstractRound] = DecisionMakingRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            sender = self.context.agent_address
            event = self.get_event()
            payload = DecisionMakingPayload(sender=sender, event=event)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def get_event(self):
        """Get the next event"""
        targeted_price = 1.2
        self.context.logger.info(f"Targeted price is {targeted_price}")
        if (self.synchronized_data.price > targeted_price):
            event = Event.TRANSACT.value
        else:
            event = Event.DONE.value
        
        self.context.logger.info(f"Event is {event}")
        return event


class TxPreparationBehaviour(
    LearningBaseBehaviour
):  # pylint: disable=too-many-ancestors
    """TxPreparationBehaviour"""

    matching_round: Type[AbstractRound] = TxPreparationRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            sender = self.context.agent_address
            tx_hash = yield from self.get_tx_hash()
            safe_tx = hash_payload_to_hex(
                safe_tx_hash=tx_hash,
                ether_value=10**18,
                safe_tx_gas=SAFE_GAS,
                to_address=self.params.transfer_target_address,
                data=TX_DATA,
            )
            payload = TxPreparationPayload(
                sender=sender, tx_submitter=None, tx_hash=safe_tx
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def get_tx_hash(self):
        """Get the tx hash"""
        # We need to prepare a 1 wei transfer from the safe to another (configurable) account.
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE, # type: ignore
            contract_address=self.synchronized_data.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction_hash",
            chain_id=GNOSIS_CHAIN_ID,
            to_address=self.params.transfer_target_address,
            data=TX_DATA,
            safe_tx_gas=SAFE_GAS,
            value=10**18
        )

        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"{response.performative.value} vs {ContractApiMessage.Performative.STATE.value}"
            )
            return None
        tx_hash_data = cast(str, response.state.body["tx_hash"])
        tx_hash = tx_hash_data[2:]
        self.context.logger.info(f"Transaction hash is {tx_hash}")
        return tx_hash


class LearningRoundBehaviour(AbstractRoundBehaviour):
    """LearningRoundBehaviour"""

    initial_behaviour_cls = APICheckBehaviour
    abci_app_cls = LearningAbciApp  # type: ignore
    behaviours: Set[Type[BaseBehaviour]] = [  # type: ignore
        APICheckBehaviour,
        DecisionMakingBehaviour,
        TxPreparationBehaviour,
    ]
