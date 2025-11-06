

import random
from typing import Set, Optional, Dict, Any
from dataclasses import dataclass


@dataclass(frozen=True)
class ASPAIssuanceData:

    issued_asns: frozenset[int]

    def is_asn_issued(self, asn: int) -> bool:
        return asn in self.issued_asns

    def get_issued_asns(self) -> Set[int]:
        return set(self.issued_asns)


class ASPAIssuanceManager:
    def select_issued_asns(self, issued_asns: Set[int]) -> ASPAIssuanceData:
        issuance_data = ASPAIssuanceData(issued_asns=issued_asns)

