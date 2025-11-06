
from .as_graphs.enums import ExtendedASGroups
from .policies import PartialIssuanceASPA, PathProb
from .scenarios.flexible_route_leak import FlexibleRouteLeak
from bgpy.simulation_framework import ScenarioConfig
from .sims import PartialIssuanceSim, RouteLeakSim
from bgpy.simulation_engine.policies.bgp.bgp_full import BGPFull

import time

pathprob_file = "test_data/prob_inference/result/202506/pathprob.txt"

deployment_percentage_tuple = (0.25, 0.5, 0.75, 1.0)
issuance_rates_tuple = (0.0, 0.25, 0.5, 0.75, 1.0)


def partial_issuance_sim():
    # ASPA
    for deployment_percentage in deployment_percentage_tuple:
        sim = PartialIssuanceSim(
            issuance_rates=issuance_rates_tuple,
            deployment_percentage=deployment_percentage,
            scenario_configs=tuple(
                [
                    ScenarioConfig(
                        AdoptPolicyCls=PartialIssuanceASPA,
                        ScenarioCls=FlexibleRouteLeak,
                        BasePolicyCls=BGPFull,
                        attacker_subcategory_attr=ExtendedASGroups.LEAKER.value,
                        victim_subcategory_attr=ExtendedASGroups.ALL_WOUT_IXPS.value,
                        adoption_subcategory_attrs=(
                            ExtendedASGroups.ALL_WOUT_IXPS.value,
                        ),
                    )
                ]
            ),
            file_path=None,
            filename="ASPA",
            parse_cpus=7,
        )
        start = time.perf_counter()
        sim.run()
        print(f"{time.perf_counter() - start}s for {sim.sim_name}")  # noqa: T201

    # pathprob
    for deployment_percentage in deployment_percentage_tuple:
        sim = PartialIssuanceSim(
            issuance_rates=issuance_rates_tuple,
            deployment_percentage=deployment_percentage,
            scenario_configs=tuple(
                [
                    ScenarioConfig(
                        AdoptPolicyCls=PathProb,
                        ScenarioCls=FlexibleRouteLeak,
                        BasePolicyCls=BGPFull,
                        attacker_subcategory_attr=ExtendedASGroups.LEAKER.value,
                        victim_subcategory_attr=ExtendedASGroups.ALL_WOUT_IXPS.value,
                        adoption_subcategory_attrs=(
                            ExtendedASGroups.ALL_WOUT_IXPS.value,
                        ),
                    )
                ]
            ),
            file_path=pathprob_file,
            filename="pathprob",
            parse_cpus=7,
        )
        start = time.perf_counter()
        sim.run()
        print(f"{time.perf_counter() - start}s for {sim.sim_name}")

if __name__ == "__main__":
    start = time.perf_counter()
    partial_issuance_sim()
    print(f"{time.perf_counter() - start}s for all sims")
