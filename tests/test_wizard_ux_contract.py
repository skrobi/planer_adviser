import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB = json.loads((ROOT / "adventure_knowledge.json").read_text(encoding="utf-8"))
WIZARD = json.loads((ROOT / "wizard_questions.json").read_text(encoding="utf-8"))

class WizardUxContractTests(unittest.TestCase):
    def test_short_mode_has_no_specialist_measurement_questions(self):
        short = [q for q in WIZARD["questions"] if "short" in q.get("modes", [])]
        forbidden = {
            "user.sweat_rate_l_per_h", "user.body_mass_kg",
            "user.gi_tolerance_high_cho", "user.gel_cho_g", "user.bar_cho_g"
        }
        self.assertFalse(forbidden.intersection(q.get("path") for q in short))

    def test_technical_measurements_are_deferred_to_trainer(self):
        deferred = set(WIZARD["meta"]["deferred_to_advanced_trainer"])
        self.assertIn("user.sweat_rate_l_per_h", deferred)
        self.assertIn("user.body_mass_kg", deferred)
        self.assertIn("user.gi_tolerance_high_cho", deferred)

    def test_short_mode_defaults_and_prefill_are_declared(self):
        self.assertEqual(WIZARD["meta"]["default_mode"], "short")
        self.assertTrue(WIZARD["meta"]["question_policy"]["ask_only_if_missing"])
        self.assertIn("rider_profile.observed", WIZARD["meta"]["prefill_sources"])
        self.assertTrue(any(q.get("ask_if_missing") for q in WIZARD["questions"]))

    def test_manual_poi_lists_are_not_asked(self):
        paths = {q.get("path") for q in WIZARD["questions"]}
        self.assertNotIn("logistics.verified_water_pois_km", paths)
        self.assertNotIn("logistics.verified_food_pois_km", paths)

    def test_luggage_mass_is_not_assumed(self):
        self.assertIsNone(WIZARD["defaults_short"]["values"]["user.luggage_mass_kg"])

    def test_profile_contract_separates_data_origins(self):
        groups = KB["profile_contract"]["groups"]
        for group in ("declared", "observed", "measured", "equipment", "preferences", "trip_specific"):
            self.assertTrue(groups[group])

if __name__ == "__main__":
    unittest.main(verbosity=2)
