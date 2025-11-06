from typing import TYPE_CHECKING, Optional
from functools import cached_property
from bgpy.simulation_framework.scenarios.custom_scenarios.accidental_route_leak import (
    AccidentalRouteLeak,
)

if TYPE_CHECKING:
    from bgpy.simulation_engine import Announcement as Ann
    from bgpy.simulation_engine import BaseSimulationEngine


class FlexibleRouteLeak(AccidentalRouteLeak):

    def _get_adopting_asns(
        self,
        override_adopting_asns: frozenset[int] | None,
        adopting_asns: frozenset[int] | None,
        engine: Optional["BaseSimulationEngine"],
    ) -> frozenset[int]:
        """
        Returns all ASNs that will be adopting the AdoptPolicyCls.

        This method removes the constraints between attackers/victims and adopting ASes.
        Adopting ASes can now be attackers, victims, or any other AS.
        """
        if override_adopting_asns is not None:
            return override_adopting_asns
        # By default use the same adopting ASes as the last scenario config
        elif adopting_asns:
            return adopting_asns
        else:
            assert engine, "either yaml or engine must be set"
            adopting_asns = self._get_randomized_adopting_asns(engine)

        return adopting_asns

    @cached_property
    def _default_adopters(self) -> frozenset[int]:
        """By default, victim always adopts"""

        return frozenset()

    @cached_property
    def _default_non_adopters(self) -> frozenset[int]:
        """By default, attacker always does not adopt"""

        return frozenset()
