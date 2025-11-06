from typing import TYPE_CHECKING

from bgpy.shared.enums import Relationships
from bgpy.simulation_engine import OnlyToCustomers
from .pathprob import PathProb

if TYPE_CHECKING:
    from bgpy.simulation_engine import Announcement as Ann


class PathProbOTC(PathProb):
    """Prevents edge ASes from paths longer than 1, and PathProb"""

    name: str = "PathProb+OTC"

    # NOTE: you could probably use multiple inheritance here, but to save some dev
    # time, I'm just going to use mixins instead
    _policy_propagate = OnlyToCustomers._policy_propagate  # noqa: SLF001

    def _valid_ann(self, ann: "Ann", from_rel: Relationships) -> bool:
        """Returns invalid if an edge AS is announcing a path longer than len 1

        otherwise returns the PathProb's _valid_ann
        """

        # NOTE: you could probably use multiple inheritance here, but to save some dev
        # time, I'm just going to use mixins instead
        if self._valid_ann_otc(ann, from_rel):
            return super()._valid_ann(ann, from_rel)
        else:
            return False

    def _valid_ann_otc(self, ann: "Ann", from_rel: Relationships) -> bool:
        """Returns False if from peer/customer when only_to_customers is set

        Taken from BGPy, no time to use and test proper multi inheritance
        """

        if (
            ann.only_to_customers
            and from_rel.value == Relationships.PEERS.value
            and ann.next_hop_asn != ann.only_to_customers
        ):
            return False
        elif ann.only_to_customers and from_rel.value == Relationships.CUSTOMERS.value:
            return False
        else:
            return True
