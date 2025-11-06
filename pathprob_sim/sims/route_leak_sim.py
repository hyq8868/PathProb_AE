
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import TYPE_CHECKING
import gc
import shutil
import time
from frozendict import frozendict
from tqdm import tqdm
from bgpy.simulation_framework import Simulation
from bgpy.simulation_framework.graphing import GraphFactory

from ..as_graphs.aspa_as_graph_constructor import ExtendedCAIDAASGraphConstructor
from ..graph_data_aggregator.issuance_rate_graph_data_aggregator import (
    IssuanceRateGraphDataAggregator,
)

if TYPE_CHECKING:
    from multiprocessing.pool import ApplyResult


class RouteLeakSim(Simulation):
    """Simulation class customized for RouteLeak simulations

    This class extends the base Simulation class to support multiple issuance rates
    while maintaining full compatibility with the BGPy framework.
    """

    def __init__(
        self,
        deployment_percentage: float = 0.25,
        *args,
        **kwargs,
    ) -> None:

        self.deployment_percentage = deployment_percentage

        custom_output_dir = (
            Path(__file__).parent.parent
            / "data"
            / "result"
            / f"route_leak_sim_{deployment_percentage}"
        )
        custom_output_dir.mkdir(parents=True, exist_ok=True)
        kwargs["output_dir"] = custom_output_dir

        cache_dir = Path(__file__).parent.parent / "data" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        kwargs["python_hash_seed"] = 0
        kwargs["as_graph_constructor_kwargs"] = frozendict(
            {
                "as_graph_collector_kwargs": frozendict(
                    {
                        "cache_dir": cache_dir,
                    }
                ),
                "as_graph_kwargs": frozendict(
                    {
                        "store_customer_cone_size": True,
                        "store_customer_cone_asns": True,
                        "store_provider_cone_size": False,
                        "store_provider_cone_asns": False,
                    }
                ),
                "tsv_path": None,
            }
        )

        kwargs["ASGraphConstructorCls"] = ExtendedCAIDAASGraphConstructor

        kwargs["percent_adoptions"] = (deployment_percentage,)

        kwargs["GraphDataAggregatorCls"] = IssuanceRateGraphDataAggregator

        super().__init__(*args, **kwargs)

        print(f"RouteLeakSim initialized:")
        print(f"  Deployment percentage: {deployment_percentage*100}%")

    def run(
        self,
        GraphFactoryCls: type[GraphFactory] | None = GraphFactory,
        graph_factory_kwargs=None,
    ) -> None:
        """Runs the simulation and write the data"""
        if graph_factory_kwargs is None:
            graph_factory_kwargs = {}

        self.ASGraphConstructorCls(**self.as_graph_constructor_kwargs).run()
        graph_data_aggregator = self._get_data()
        graph_data_aggregator.write_data(
            csv_path=self.csv_path, pickle_path=self.pickle_path
        )
        del graph_data_aggregator
        gc.collect()
        shutil.rmtree(self._tqdm_tracking_dir)
