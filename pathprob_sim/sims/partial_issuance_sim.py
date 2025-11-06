from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import TYPE_CHECKING, Tuple
import gc
import shutil
import time
from frozendict import frozendict
from tqdm import tqdm
from bgpy.simulation_framework import Simulation
from bgpy.simulation_framework.graph_data_aggregator import (
    GraphDataAggregator,
)
from bgpy.simulation_framework.graphing import GraphFactory

from ..as_graphs.aspa_as_graph_constructor import ExtendedCAIDAASGraphConstructor

from ..graph_data_aggregator.issuance_rate_graph_data_aggregator import (
    IssuanceRateGraphDataAggregator,
)

if TYPE_CHECKING:
    from multiprocessing.pool import ApplyResult


class PartialIssuanceSim(Simulation):

    def __init__(
        self,
        issuance_rates: Tuple[float, ...] = (
            0.0,
            0.05,
            0.1,
            0.15,
            0.2,
            0.25,
            0.3,
            0.35,
            0.4,
            0.45,
            0.5,
            0.55,
            0.6,
            0.65,
            0.7,
            0.75,
            0.8,
            0.85,
            0.9,
            0.95,
            1.0,
        ),
        filename: str = "aspa",
        deployment_percentage: float = 0.25,
        file_path: str | None = None,
        *args,
        **kwargs,
    ) -> None:
        # Set up issuance rates and deployment percentage
        self.issuance_rates = issuance_rates
        self.deployment_percentage = deployment_percentage
        self.file_path = file_path

        from pathlib import Path

        custom_output_dir = (
            Path(__file__).parent.parent
            / "data"
            / "result"
            / f"partial_issuance_sim_{deployment_percentage}"
            / f"{filename}"
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
                        # Store provider cone data for ASPA
                        "store_customer_cone_size": True,
                        "store_customer_cone_asns": True,
                        "store_provider_cone_size": False,
                        "store_provider_cone_asns": False,
                    }
                ),
                "tsv_path": None,
            }
        )

        # Use extended AS graph constructor
        kwargs["ASGraphConstructorCls"] = ExtendedCAIDAASGraphConstructor

        kwargs["percent_adoptions"] = (deployment_percentage,)

        kwargs["GraphDataAggregatorCls"] = IssuanceRateGraphDataAggregator

        super().__init__(*args, **kwargs)
        self.parse_cpus = kwargs["parse_cpus"]
        print(f"parse_cpus: {self.parse_cpus}")

        print(f"PartialIssuanceSim initialized:")
        print(f"  Deployment percentage: {deployment_percentage*100}%")
        print(f"  Issuance rates: {[f'{r*100}%' for r in issuance_rates]}")
        if file_path is not None:
            print(f"  Pathprob data file: {file_path}")
        else:
            print(f"  Pathprob data file: None (no pathprob data)")

    def run(
        self,
        # GraphFactoryCls: type[GraphFactory] | None = IssuanceRateGraphFactory,
        GraphFactoryCls: type[GraphFactory] | None = GraphFactory,
        graph_factory_kwargs=None,
    ) -> None:
        """Runs the simulation and write the data"""
        if graph_factory_kwargs is None:
            graph_factory_kwargs = {}

        # Cache the CAIDA graph
        self.ASGraphConstructorCls(**self.as_graph_constructor_kwargs).run()
        graph_data_aggregator = self._get_data()
        graph_data_aggregator.write_data(
            csv_path=self.csv_path, pickle_path=self.pickle_path
        )
        # self._graph_data(GraphFactoryCls, graph_factory_kwargs)
        # This object holds a lot of memory, good to get rid of it
        del graph_data_aggregator
        gc.collect()
        shutil.rmtree(self._tqdm_tracking_dir)

    def _run_chunk(self, chunk_id: int, trials: list[int]) -> GraphDataAggregator:
        """Runs a chunk of trial inputs"""
        engine = self._get_engine_for_run_chunk()

        if self.file_path is not None:
            engine.as_graph.setup_pathprob_data(self.file_path)

        import random

        random.seed(f"{chunk_id}issue")
        asn_list = [as_obj.asn for as_obj in engine.as_graph]
        random.shuffle(asn_list)
        issued_asns_map = {
            current_issuance_rate: frozenset(
                asn_list[: int(len(asn_list) * current_issuance_rate)]
            )
            for current_issuance_rate in self.issuance_rates
        }

        self._seed_random(seed_suffix=str(chunk_id))

        graph_data_aggregator = self.GraphDataAggregatorCls(
            graph_categories=self.graph_categories
        )
        reuse_attacker_asns = self._get_reuse_attacker_asns()
        reuse_victim_asns = self._get_reuse_victim_asns()
        reuse_adopting_asns = self._get_reuse_adopting_asns()

        for trial_index, trial in self._get_run_chunk_iter(trials):
            # Use the same attacker victim pairs across all issuance rates for this trial
            trial_attacker_asns = None
            trial_victim_asns = None
            percent_adopt = self.deployment_percentage
            adopting_asns = None

            for issuance_rate_index, current_issuance_rate in enumerate(
                self.issuance_rates
            ):

                engine.as_graph.set_aspa_issuance_data(
                    issued_asns_map[current_issuance_rate]
                )

                for scenario_config in self.scenario_configs:
                    # Create the scenario for this trial
                    assert scenario_config.ScenarioCls, "ScenarioCls is None"
                    scenario = scenario_config.ScenarioCls(
                        scenario_config=scenario_config,
                        percent_adoption=percent_adopt,
                        engine=engine,
                        attacker_asns=trial_attacker_asns,
                        victim_asns=trial_victim_asns,
                        adopting_asns=adopting_asns,
                    )
                    scenario.setup_engine(engine)
                    for propagation_round in range(scenario_config.propagation_rounds):
                        self._single_engine_run(
                            engine=engine,
                            percent_adopt=current_issuance_rate,
                            trial=trial,
                            scenario=scenario,
                            propagation_round=propagation_round,
                            graph_data_aggregator=graph_data_aggregator,
                        )
                    
                    if reuse_attacker_asns:
                        trial_attacker_asns = scenario.attacker_asns
                    if reuse_victim_asns:
                        trial_victim_asns = scenario.victim_asns
                    if reuse_adopting_asns:
                        adopting_asns = scenario.adopting_asns

                # Used to track progress with tqdm
                total_completed = (
                    trial_index * len(self.issuance_rates) + issuance_rate_index + 1
                )
                self._write_tqdm_progress(chunk_id, total_completed)

        self._write_tqdm_progress(chunk_id, len(trials) * len(self.issuance_rates))

        return graph_data_aggregator

    def _get_mp_results(self) -> list[GraphDataAggregator]:
        """Get results from multiprocessing

        Previously used starmap, but now we have tqdm
        """

        # Pool is much faster than ProcessPoolExecutor
        with Pool(self.parse_cpus) as p:
            # return p.starmap(self._run_chunk, enumerate(self._get_chunks(parse_cpus)))
            chunks = self._get_chunks(self.parse_cpus)
            desc = f"Simulating {self.output_dir.name}"
            total = sum(len(x) for x in chunks) * len(self.issuance_rates)
            with tqdm(total=total, desc=desc) as pbar:
                tasks: list[ApplyResult[GraphDataAggregator]] = [
                    p.apply_async(self._run_chunk, x) for x in enumerate(chunks)
                ]
                completed: list[GraphDataAggregator] = []
                while tasks:
                    completed, tasks = self._get_completed_and_tasks(completed, tasks)
                    self._update_tqdm_progress_bar(pbar)
                    time.sleep(0.5)
        return completed
