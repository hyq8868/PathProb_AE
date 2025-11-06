"""
Issuance rate graph data aggregator

Extends GraphDataAggregator class to handle issuance rate data instead of deployment rate data.
Minimizes rewriting by only changing deployment rate to issuance rate, keeping other logic unchanged.
Also supports LIR and LCR metrics calculation.

LIR (Leak Impact Ratio): attacker_success / (attacker_success + victim_success)
LCR (Leak Coverage Ratio): victim_success / (attacker_success + victim_success + disconnected)
"""

from collections import defaultdict
from typing import Any
from bgpy.simulation_framework.graph_data_aggregator.graph_data_aggregator import (
    GraphDataAggregator,
)
from bgpy.simulation_framework.graph_data_aggregator.graph_category import GraphCategory
from bgpy.shared.enums import ASGroups, InAdoptingASNs, Plane, Outcomes
from bgpy.simulation_framework.graph_data_aggregator.trial_data import TrialData


LIR_OUTCOME = 5  # Leak Impact Ratio
LCR_OUTCOME = 6  # Leak Coverage Ratio


class LIRLCRTrialData(TrialData):
    """TrialData that supports LIR and LCR metrics calculation"""

    def __init__(self, graph_category: GraphCategory) -> None:
        super().__init__(graph_category)
        self._attacker_success_count = 0
        self._victim_success_count = 0
        self._disconnected_count = 0
        self._total_affected_count = 0

    def get_percent(self) -> float | None:
        """Override percentage calculation method to support LIR and LCR metrics"""
        if self._numerator == 0 and self._denominator == 0:
            return None

        if self.graph_category.outcome == LIR_OUTCOME:
            if self._attacker_success_count + self._victim_success_count == 0:
                return None
            return (
                self._attacker_success_count
                * 100
                / (self._attacker_success_count + self._victim_success_count)
            )

        elif self.graph_category.outcome == LCR_OUTCOME:
            if self._total_affected_count == 0:
                return None
            return self._victim_success_count * 100 / self._total_affected_count

        else:
            return self._numerator * 100 / self._denominator

    def add_data(
        self,
        *,
        as_obj,
        engine,
        scenario,
        ctrl_plane_outcome,
        data_plane_outcome,
    ):
        within_denom = self._add_denominator(
            as_obj=as_obj,
            engine=engine,
            scenario=scenario,
            ctrl_plane_outcome=ctrl_plane_outcome,
            data_plane_outcome=data_plane_outcome,
        )

        if within_denom:
            if self.graph_category.plane == Plane.DATA:
                outcome = data_plane_outcome
            elif self.graph_category.plane == Plane.CTRL:
                outcome = ctrl_plane_outcome
            else:
                raise NotImplementedError

            if self.graph_category.outcome == LIR_OUTCOME:
                if outcome == Outcomes.ATTACKER_SUCCESS.value:
                    self._attacker_success_count += 1
                elif outcome == Outcomes.VICTIM_SUCCESS.value:
                    self._victim_success_count += 1
            elif self.graph_category.outcome == LCR_OUTCOME:
                if outcome == Outcomes.ATTACKER_SUCCESS.value:
                    self._attacker_success_count += 1
                    self._total_affected_count += 1
                elif outcome == Outcomes.VICTIM_SUCCESS.value:
                    self._victim_success_count += 1
                    self._total_affected_count += 1
                elif outcome == Outcomes.DISCONNECTED.value:
                    self._disconnected_count += 1
                    self._total_affected_count += 1

            if self.graph_category.outcome not in [LIR_OUTCOME, LCR_OUTCOME]:
                self._add_numerator(
                    as_obj=as_obj,
                    engine=engine,
                    scenario=scenario,
                    ctrl_plane_outcome=ctrl_plane_outcome,
                    data_plane_outcome=data_plane_outcome,
                )


class IssuanceRateGraphDataAggregator(GraphDataAggregator):
    """Extended graph data aggregator for handling issuance rate data

    This class inherits from GraphDataAggregator and only overrides necessary methods
    to support issuance rate. All other logic (data collection, aggregation, saving, etc.)
    remains the same as the parent class. Also supports LIR and LCR metrics calculation.
    """

    def __init__(self, *args, **kwargs):
        """Initialize issuance rate graph data aggregator"""
        super().__init__(*args, **kwargs)

    def _get_percent_adopt(self, data_point_key) -> float:
        """Override method to get deployment rate, returns issuance rate instead

        This is the key method that replaces deployment rate with issuance rate
        """
        return float(data_point_key.percent_adopt)

    def _get_all_graph_categories(self):
        """Get all graph categories, including LIR and LCR metrics"""
        from bgpy.simulation_framework.utils import get_all_graph_categories

        original_categories = list(get_all_graph_categories())
        lir_lcr_categories = []
        for plane in [Plane.DATA]:
            for as_group in [ASGroups.ALL_WOUT_IXPS]:
                for outcome in [LIR_OUTCOME, LCR_OUTCOME]:
                    for in_adopting_asns_enum in list(InAdoptingASNs):
                        lir_lcr_categories.append(
                            GraphCategory(
                                plane=plane,
                                as_group=as_group,
                                outcome=outcome,
                                in_adopting_asns=in_adopting_asns_enum,
                            )
                        )

        return original_categories + lir_lcr_categories

    def aggregate_and_store_trial_data(
        self,
        *,
        engine,
        percent_adopt,
        trial,
        scenario,
        propagation_round,
        outcomes,
    ) -> None:
        """Override method to aggregate and store trial data using LIRLCRTrialData"""

        all_categories = self._get_all_graph_categories()

        trial_datas = [LIRLCRTrialData(x) for x in all_categories]
        self._aggregate_trial_data(
            trial_datas=trial_datas, engine=engine, scenario=scenario, outcomes=outcomes
        )

        from bgpy.simulation_framework.graph_data_aggregator.data_point_key import (
            DataPointKey,
        )

        data_point_key = DataPointKey(
            propagation_round=propagation_round,
            percent_adopt=percent_adopt,
            scenario_config=scenario.scenario_config,
        )

        for trial_data in trial_datas:
            percent = trial_data.get_percent()
            if percent is not None:
                if trial_data.graph_category not in self.data:
                    self.data[trial_data.graph_category] = defaultdict(list)
                self.data[trial_data.graph_category][data_point_key].append(percent)

    def __add__(self, other: Any) -> "IssuanceRateGraphDataAggregator":
        """Override __add__ method to support merging of LIR and LCR metrics"""
        if isinstance(other, IssuanceRateGraphDataAggregator):
            all_categories = self._get_all_graph_categories()

            new_data: dict = {x: defaultdict(list) for x in all_categories}
            for obj in (self, other):
                for graph_category, data_dict in obj.data.items():
                    for data_point_key, percents in data_dict.items():
                        new_data[graph_category][data_point_key].extend(percents)

            return self.__class__(data=new_data, graph_categories=all_categories)
        else:
            return NotImplemented

    def get_csv_rows(self) -> list[dict[str, Any]]:
        """Override get_csv_rows method to support CSV output for LIR and LCR metrics"""
        from statistics import mean

        rows = []
        for graph_category, data_dict in self.data.items():
            for data_point_key, percent_list in data_dict.items():
                if percent_list:
                    if graph_category.outcome == LIR_OUTCOME:
                        outcome_name = "LIR"
                    elif graph_category.outcome == LCR_OUTCOME:
                        outcome_name = "LCR"
                    else:
                        outcome_name = graph_category.outcome.name
                    scenario_cls_name = (
                        data_point_key.scenario_config.ScenarioCls.__name__
                    )
                    adopting_policy_cls_name = (
                        data_point_key.scenario_config.AdoptPolicyCls.__name__
                    )
                    base_policy_cls_name = (
                        data_point_key.scenario_config.BasePolicyCls.__name__
                    )

                    rows.append(
                        {
                            "scenario_cls": scenario_cls_name,
                            "AdoptingPolicyCls": adopting_policy_cls_name,
                            "BasePolicyCls": base_policy_cls_name,
                            "in_adopting_asns": graph_category.in_adopting_asns.value,
                            "outcome_type": graph_category.plane.name,
                            "as_group": graph_category.as_group.value,
                            "outcome": outcome_name,
                            "percent_adopt": data_point_key.percent_adopt,
                            "propagation_round": data_point_key.propagation_round,
                            "value": mean(percent_list) if percent_list else None,
                            "yerr": self._get_yerr(percent_list),
                            "scenario_config_label": (
                                data_point_key.scenario_config.csv_label
                            ),
                            "scenario_label": data_point_key.scenario_config.scenario_label,
                        }
                    )
        return rows
