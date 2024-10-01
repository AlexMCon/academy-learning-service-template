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

"""This module contains the shared state for the abci skill of LearningAbciApp."""

from typing import Any, TypedDict

from packages.valory.skills.abstract_round_abci.models import BaseParams
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.learning_abci.rounds import LearningAbciApp


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls = LearningAbciApp


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool


class Params(BaseParams):
    """Parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object."""
        self.api_url = self._ensure(
            "api_url", kwargs, str
        )
        self.agent_api_key = self._ensure(
            "agent_api_key", kwargs, str
        )
        self.wxdai_contract_address = self._ensure(
            "wxdai_contract_address", kwargs, str
        )
        self.agent_party = self._ensure(
            "agent_party", kwargs, str
        )
        self.transfer_target_address = self._ensure(
            "transfer_target_address", kwargs, str
        )
        self.check_approval_contract_address = self._ensure(
            "check_approval_contract_address", kwargs, str
        )

        super().__init__(*args, **kwargs)
        
class AutonolasData(TypedDict):
    usd: float

class CoinData(TypedDict):
    autonolas: AutonolasData