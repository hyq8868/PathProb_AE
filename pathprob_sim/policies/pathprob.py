from typing import TYPE_CHECKING

from bgpy.shared.enums import Relationships
from bgpy.simulation_engine.policies.bgp.bgp_full import BGPFull
from bgpy.simulation_engine.policies.rov import ROV

if TYPE_CHECKING:
    from bgpy.simulation_engine import Announcement as Ann


class PathProb(ROV, BGPFull):
    name: str = "PathProb"
    probability_threshold: float = 0.4

    def is_asn_issued(self, asn: int) -> bool:
        if hasattr(self.as_.as_graph, "is_asn_issued"):
            return self.as_.as_graph.is_asn_issued(asn)
        return False

    def _valid_ann(self, ann: "Ann", from_rel: Relationships) -> bool:

        if not self._next_hop_valid(ann):
            return False

        path = ann.as_path
        prob = 1.0
        c2p0 = 1.0
        for i in range(len(path) - 1):
            p2c, _, c2p = self._asrel_prob(path[i], path[i + 1])
            prob = min(p2c + c2p0 - p2c * c2p0, prob)
            c2p0 = c2p
        return prob >= self.probability_threshold and super()._valid_ann(ann, from_rel)

    def _next_hop_valid(self, ann: "Ann") -> bool:

        return ann.next_hop_asn == ann.as_path[0]

    def _asrel_prob(self, asn1: int, asn2: int) -> (float, float, float):
        p2c = (1.0, 0.0, 0.0)
        c2p = (0.0, 0.0, 1.0)
        p2p = (0.0, 1.0, 0.0)

        if self.is_asn_issued(asn1) and self.is_asn_issued(asn2):
            if asn1 in self.as_.as_graph.as_dict[asn2].provider_asns:
                return p2c
            elif asn2 in self.as_.as_graph.as_dict[asn1].provider_asns:
                return c2p
            else:
                return p2p
        elif (
            self.is_asn_issued(asn1)
            and asn2 in self.as_.as_graph.as_dict[asn1].provider_asns
        ):
            return c2p
        elif (
            self.is_asn_issued(asn2)
            and asn1 in self.as_.as_graph.as_dict[asn2].provider_asns
        ):
            return p2c
        else:
            return self.as_.as_graph.get_asrel_prob(asn1, asn2)
