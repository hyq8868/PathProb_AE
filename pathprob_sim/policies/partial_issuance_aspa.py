from typing import TYPE_CHECKING

from bgpy.shared.enums import Relationships
from bgpy.simulation_engine.policies.bgp.bgp_full import BGPFull
from bgpy.simulation_engine.policies.aspa.aspa import ASPA

if TYPE_CHECKING:
    from bgpy.simulation_engine import Announcement as Ann


class PartialIssuanceASPA(ASPA, BGPFull):
    name: str = "PartialIssuanceASPA"

    def is_asn_issued(self, asn: int) -> bool:
        if hasattr(self.as_.as_graph, "is_asn_issued"):
            return self.as_.as_graph.is_asn_issued(asn)
        return False

    def _provider_check(self, asn1: int, asn2: int) -> bool:

        cur_as_obj = self.as_.as_graph.as_dict.get(asn1)
        if cur_as_obj and isinstance(cur_as_obj.policy, PartialIssuanceASPA):
            # Only check provider relationships if this AS has ASPA records
            if not self.is_asn_issued(asn1):
                # No ASPA records for this AS, treat as "No Attestation"
                return True

            next_as_obj = self.as_.as_graph.as_dict.get(asn2)
            next_asn = next_as_obj.asn if next_as_obj else next_as_obj
            if next_asn not in cur_as_obj.provider_asns:
                return False

        return True
