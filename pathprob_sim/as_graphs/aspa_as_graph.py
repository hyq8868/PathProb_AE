from typing import Optional, Set, Dict, Any, Callable
from frozendict import frozendict
from bgpy.as_graphs.caida_as_graph.caida_as_graph import CAIDAASGraph
from bgpy.as_graphs.base.as_graph.base_as import AS
from bgpy.shared.enums import ASGroups


from .enums import ExtendedASGroups
from .base.as_graph.base_as_extension import ExtendedAS

from .asrel_object.pathprob_data import PathProbData

class ExtendedCAIDAASGraph(CAIDAASGraph):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.aspa_issuance_data: frozenset[int] = frozenset()
        self.pathprob_data: Optional[PathProbData] = None

    def _gen_graph(self, as_graph_info, BaseASCls, BasePolicyCls):
        return super()._gen_graph(as_graph_info, ExtendedAS, BasePolicyCls)

    def set_aspa_issuance_data(self, issuance_data: frozenset[int]) -> None:
        self.aspa_issuance_data = issuance_data

    def get_pathprob_data(self) -> Optional[PathProbData]:
        return self.pathprob_data

    def get_aspa_issuance_data(self) -> frozenset[int]:
        return self.aspa_issuance_data

    def is_asn_issued(self, asn: int) -> bool:
        return asn in self.aspa_issuance_data

    def get_asrel_prob(self, asn1: int, asn2: int) -> (float, float, float):
        return self.pathprob_data.get_prob(asn1, asn2)

    def get_issued_asns(self) -> Set[int]:
        return self.aspa_issuance_data

    def setup_pathprob_data(self, file_path: Optional[str]) -> None:
        if file_path is None:
            return
        self.pathprob_data = PathProbData.load_asrel_prob_from_file(file_path)

        
    @property
    def _default_as_group_filters(
        self,
    ) -> frozendict[str, Callable[["ExtendedCAIDAASGraph"], frozenset[AS]]]:
        """Returns the default filter functions for AS groups"""

        def ixp_filter(as_graph: "ExtendedCAIDAASGraph") -> frozenset[AS]:
            return frozenset(x for x in as_graph if x.ixp)

        def stub_no_ixp_filter(as_graph: "ExtendedCAIDAASGraph") -> frozenset[AS]:
            return frozenset(x for x in as_graph if x.stub and not x.ixp)

        def multihomed_no_ixp_filter(as_graph: "ExtendedCAIDAASGraph") -> frozenset[AS]:
            return frozenset(x for x in as_graph if x.multihomed and not x.ixp)

        def stubs_or_multihomed_no_ixp_filter(
            as_graph: "ExtendedCAIDAASGraph",
        ) -> frozenset[AS]:
            return frozenset(
                x for x in as_graph if (x.stub or x.multihomed) and not x.ixp
            )

        def input_clique_no_ixp_filter(
            as_graph: "ExtendedCAIDAASGraph",
        ) -> frozenset[AS]:
            return frozenset(x for x in as_graph if x.input_clique and not x.ixp)

        def etc_no_ixp_filter(as_graph: "ExtendedCAIDAASGraph") -> frozenset[AS]:
            return frozenset(
                x
                for x in as_graph
                if not (x.stub or x.multihomed or x.input_clique or x.ixp)
            )

        def transit_no_ixp_filter(as_graph: "ExtendedCAIDAASGraph") -> frozenset[AS]:
            return frozenset(x for x in as_graph if x.transit and not x.ixp)

        def all_no_ixp_filter(as_graph: "ExtendedCAIDAASGraph") -> frozenset[AS]:
            return frozenset(list(as_graph))

        def leaker_no_ixp_filter(as_graph: "ExtendedCAIDAASGraph") -> frozenset[AS]:
            """Filter out leaker type ASes (excluding IXP)"""
            return frozenset(x for x in as_graph if x.leaker and not x.ixp)

        return frozendict(
            {
                ExtendedASGroups.IXPS.value: ixp_filter,
                ExtendedASGroups.STUBS.value: stub_no_ixp_filter,
                ExtendedASGroups.MULTIHOMED.value: multihomed_no_ixp_filter,
                ExtendedASGroups.STUBS_OR_MH.value: stubs_or_multihomed_no_ixp_filter,
                ExtendedASGroups.INPUT_CLIQUE.value: input_clique_no_ixp_filter,
                ExtendedASGroups.ETC.value: etc_no_ixp_filter,
                ExtendedASGroups.TRANSIT.value: transit_no_ixp_filter,
                ExtendedASGroups.ALL_WOUT_IXPS.value: all_no_ixp_filter,
                ExtendedASGroups.LEAKER.value: leaker_no_ixp_filter,
            }
        )
