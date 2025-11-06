from functools import cached_property
from bgpy.as_graphs.base.as_graph.base_as import AS as BaseAS


class ExtendedAS(BaseAS):
    @cached_property
    def leaker(self) -> bool:
        """Returns True if AS is a potential leaker (has multiple peers or providers)"""
        return len(self.peers) + len(self.providers) > 1
