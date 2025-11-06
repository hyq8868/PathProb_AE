from bgpy.as_graphs.caida_as_graph.caida_as_graph_constructor import (
    CAIDAASGraphConstructor,
)
from bgpy.as_graphs.caida_as_graph.caida_as_graph import CAIDAASGraph

from .custom_caida_as_graph_collector import CustomCAIDAASGraphCollector
from bgpy.as_graphs.base import (
    PeerLink,
)
from bgpy.as_graphs.base import CustomerProviderLink as CPLink


class CustomCAIDAASGraphConstructor(CAIDAASGraphConstructor):
    
    def __init__(
        self,
        ASGraphCollectorCls=CustomCAIDAASGraphCollector,
        ASGraphCls=CAIDAASGraph,
        **kwargs
    ) -> None:
        super().__init__(
            ASGraphCollectorCls=ASGraphCollectorCls, ASGraphCls=ASGraphCls, **kwargs
        )

    #################
    # Parsing funcs #
    #################

    def _extract_provider_customers(
        self, line: str, cp_links: set[CPLink], invalid_asns: frozenset[int]
    ) -> None:
        """Extracts provider customers: <provider-as>|<customer-as>|-1"""

        provider_asn, customer_asn, _ = line.split("|")
        if all(int(x) not in invalid_asns for x in (provider_asn, customer_asn)):
            cp_links.add(
                CPLink(customer_asn=int(customer_asn), provider_asn=int(provider_asn))
            )

    def _extract_peers(
        self, line: str, peer_links: set[PeerLink], invalid_asns: frozenset[int]
    ) -> None:
        """Extracts peers: <peer-as>|<peer-as>|0|<source>"""

        peer1_asn, peer2_asn, _ = line.split("|")
        if all(int(x) not in invalid_asns for x in (peer1_asn, peer2_asn)):
            peer_links.add(PeerLink(int(peer1_asn), int(peer2_asn)))
