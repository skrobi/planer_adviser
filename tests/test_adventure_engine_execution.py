import json
import unittest
from pathlib import Path
from adventure_engine_runner import execute
from verify_adventure_engine import verify

ROOT = Path(__file__).resolve().parents[1]
KB = json.loads((ROOT / "adventure_knowledge.json").read_text(encoding="utf-8"))
SCENARIOS = json.loads((ROOT / "tests" / "scenarios.json").read_text(encoding="utf-8"))["scenarios"]

class ExecutableAdventureEngineTests(unittest.TestCase):
    def test_all_ten_scenarios_match_expectations(self):
        report = verify(KB, SCENARIOS)
        failures = [f"{c['id']}: {'; '.join(c['problems'])}" for c in report["cases"] if not c["passed"]]
        self.assertEqual(failures, [])

    def test_engine_executes_models_from_json(self):
        result = execute(KB, SCENARIOS[4])
        self.assertAlmostEqual(result["derived"]["stage"]["fluid_target_l_per_h_operational"], 1.2)
        self.assertFalse(result["derived"]["plan"]["hydration"]["satisfied"])
        self.assertIn("nut_hydration_carry_insufficient", result["fired_rule_ids"])

    def test_missing_values_are_not_silently_imputed(self):
        result = execute(KB, next(s for s in SCENARIOS if s["id"] == "S09_missing_critical_inputs"))
        self.assertNotIn("body_mass_kg", result["derived"]["user"])
        self.assertEqual(result["derived"]["stage"]["input_completeness"], "partial_load_inputs")


    def test_s01_composes_three_user_facing_cards_without_inventing_data(self):
        result = execute(KB, next(s for s in SCENARIOS if s["id"] == "S01_beginner_300km_no_sleep"))
        cards = result["composed_recommendations"]
        self.assertEqual([c["id"] for c in cards], ["safety_and_staging", "nutrition", "hydration"])
        safety, nutrition, hydration = cards
        self.assertEqual(safety["severity"], "critical")
        self.assertIn("wymaga zmiany", safety["summary"])
        self.assertNotIn("3 etapy", " ".join(safety["details"] + safety["actions"]))
        self.assertEqual(nutrition["data_status"], "user_input_required")
        self.assertIn("Nie zadeklarowano", nutrition["summary"])
        self.assertNotIn("zapas (", nutrition["summary"])
        self.assertEqual(hydration["data_status"], "estimated")
        self.assertTrue(any("nie potwierdza" in x for x in hydration["details"]))

    def test_declared_pack_is_distinguished_from_unknown_pack(self):
        s01 = next(s for s in SCENARIOS if s["id"] == "S01_beginner_300km_no_sleep")
        s07 = next(s for s in SCENARIOS if s["id"] == "S07_declared_120g_CHO_pack")
        unknown = execute(KB, s01)["composed_recommendations"]
        declared = execute(KB, s07)["composed_recommendations"]
        self.assertEqual(next(c for c in unknown if c["id"] == "nutrition")["data_status"], "user_input_required")
        self.assertIn("Zadeklarowany zapas", next(c for c in declared if c["id"] == "nutrition")["summary"])

if __name__ == "__main__":
    unittest.main()
