from typing import TYPE_CHECKING

from bgpy.shared.enums import Relationships
from bgpy.simulation_engine import EdgeFilter
from .pathprob_otc import PathProbOTC

if TYPE_CHECKING:
    from bgpy.simulation_engine import Announcement as Ann


class PathProbOTCEdge(PathProbOTC):
    """Prevents edge ASes from paths longer than 1, and PathProb"""

    name: str = "PathProb+OTC+EdgeFilter"


def _valid_ann(self, ann: "Ann", from_rel: "Relationships") -> bool:

    if EdgeFilter._valid_edge_ann(self, ann, from_rel):  
        return super()._valid_ann(ann, from_rel)
    else:
        return False
