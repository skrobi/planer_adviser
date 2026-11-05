import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB = json.loads((ROOT / "adventure_knowledge.json").read_text(encoding="utf-8"))
WIZARD = json.loads((ROOT / "wizard_questions.json").read_text(encoding="utf-8"))


class Stage5ContractTests(unittest.TestCase):
    def test_versions_are_aligned(self):
        self.assertEqual(WIZARD["meta"]["kb_version_target"], KB["meta"]["knowledge_version"])

    def test_moving_stops_sleep_are_separate(self):
        contract = KB["stage5_contracts"]["canonical_stage"]
        self.assertEqual(contract["moving_time"], "stage.estimated_moving_time_hours")
        self.assertEqual(contract["stops"], "stage.planned_stops_hours")
        self.assertEqual(contract["sleep"], "stage.planned_sleep_hours")
        self.assertIn("moving time only", contract["time_semantics"])

    def test_trip_aggregation_preserves_unknowns(self):
        trip = KB["stage5_contracts"]["trip_accounting"]
        self.assertIn("trip.accounting_completeness", trip["outputs"])
        self.assertIn("unknown if any required stage moving time is absent", trip["aggregation"]["moving_time"])
        self.assertIn("never substitute missing components with zero", trip["aggregation"]["elapsed"])

    def test_stage_load_is_transparent_not_a_fatigue_score(self):
        load = KB["stage5_contracts"]["stage_load_and_recovery"]
        self.assertIn("plan.trip_accounting.load_ledger", load["outputs"])
        self.assertIn("Do not calculate a single cumulative fatigue score", load["method"])
        self.assertIn("unvalidated_cumulative_fatigue_score", KB["stage5_contracts"]["trip_accounting"]["forbidden_outputs"])

    def test_poi_presence_never_proves_resupply(self):
        poi = KB["stage5_contracts"]["poi_access"]
        rules = " ".join(poi["eligibility_rules"]).lower()
        self.assertIn("water volume", rules)
        self.assertIn("cho quantity", rules)
        self.assertIn("unknown hours", rules)
        self.assertIn("capacity", rules)
        self.assertIn("detour", rules)

    def test_ridemore_owns_poi_taxonomy(self):
        self.assertIn("Ridemore owns POI category taxonomy", KB["stage5_contracts"]["poi_access"]["adapter_boundary"])

    def test_all_new_contract_paths_are_declared(self):
        paths = KB["data_dictionary"]["paths"]
        required = [
            "trip.stage_sequence", "stage.id", "stage.ordinal", "stage.start_km",
            "stage.end_km", "stage.estimated_moving_time_hours",
            "stage.planned_stops_hours", "stage.planned_sleep_hours",
            "trip.total_moving_hours", "trip.total_stops_hours",
            "trip.total_sleep_hours", "trip.total_elapsed_hours",
            "trip.accounting_completeness", "logistics.poi_candidates",
            "poi.id", "poi.arrival_time_local", "poi.open_status_at_arrival",
            "poi.water_volume_l", "poi.food_cho_g", "poi.capacity_status",
            "poi.detour_distance_km", "poi.fetched_at", "poi.valid_until",
            "plan.trip_accounting.load_ledger", "plan.poi_access.status"
        ]
        self.assertEqual(sorted(set(required) - set(paths)), [])


    def test_inventory_event_resources_are_explicit(self):
        events = KB["stage5_contracts"]["inventory_ledger"]["event_types"]
        self.assertEqual(events["water_refill"]["resource"], "water_l")
        self.assertEqual(events["cho_resupply"]["resource"], "cho_g")
        self.assertEqual(events["water_loss"]["resource"], "water_l")
        self.assertEqual(events["cho_loss"]["resource"], "cho_g")


    def test_poi_access_requires_verified_fresh_open_and_capacity(self):
        from adventure_engine_runner import assess_poi_access
        ctx={"logistics":{"poi_candidates":[
            {"id":"good","verification_status":"verified","freshness_status":"fresh","open_status_at_arrival":"open_confirmed","route_km":20,"detour_distance_km":0.2,"water_volume_l":2,"water_capacity_status":"confirmed_sufficient"},
            {"id":"closed","verification_status":"verified","freshness_status":"fresh","open_status_at_arrival":"closed_confirmed","route_km":30,"detour_distance_km":0.1,"water_volume_l":3,"water_capacity_status":"confirmed_sufficient"},
            {"id":"stale","verification_status":"official","freshness_status":"stale","open_status_at_arrival":"open_confirmed","route_km":40,"detour_distance_km":0,"food_cho_g":80,"food_capacity_status":"confirmed_sufficient"},
            {"id":"unknown_qty","verification_status":"verified","freshness_status":"fresh","open_status_at_arrival":"open_confirmed","route_km":50,"detour_distance_km":0.1,"food_cho_g":None,"food_capacity_status":"unknown"}
        ]}}
        assess_poi_access(KB,ctx)
        access=ctx["plan"]["poi_access"]
        self.assertEqual(access["eligible_poi_ids"],["good"])
        self.assertEqual(access["confirmed_water_poi_ids"],["good"])
        self.assertIn("closed",access["excluded_poi_ids"])
        self.assertIn("stale",access["excluded_poi_ids"])

    def test_poi_candidates_are_not_automatically_inventory_events(self):
        from adventure_engine_runner import assess_poi_access
        ctx={"logistics":{"poi_candidates":[{"id":"good","verification_status":"verified","freshness_status":"fresh","open_status_at_arrival":"open_confirmed","route_km":20,"detour_distance_km":0,"water_volume_l":2,"water_capacity_status":"confirmed_sufficient"}]}}
        assess_poi_access(KB,ctx)
        self.assertNotIn("inventory_ledger",ctx.get("plan",{}).get("trip_accounting",{}))
        self.assertEqual(ctx["plan"]["poi_access"]["eligible_poi_ids"],["good"])

    def test_short_wizard_policy_is_explicit(self):
        self.assertTrue(WIZARD["meta"]["question_policy"]["ask_only_if_missing"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
