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

if __name__ == "__main__":
    unittest.main()
