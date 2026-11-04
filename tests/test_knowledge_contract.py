import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB = json.loads((ROOT / "adventure_knowledge.json").read_text(encoding="utf-8"))
WIZARD = json.loads((ROOT / "wizard_questions.json").read_text(encoding="utf-8"))

class KnowledgeContractTests(unittest.TestCase):
    def test_versions_are_aligned(self):
        self.assertEqual(WIZARD["meta"]["kb_version_target"], KB["meta"]["knowledge_version"])

    def test_every_wizard_path_is_declared(self):
        paths = WIZARD.get("data_dictionary", {}).get("paths", KB["data_dictionary"]["paths"])
        declared = KB["data_dictionary"]["paths"]
        missing = sorted({q["path"] for q in WIZARD["questions"] if q.get("path") and q["path"] not in declared})
        self.assertEqual(missing, [])

    def test_every_decision_tree_model_exists(self):
        known = set(KB["models"])
        for phase in KB["decision_tree"]["phases"]:
            for model in phase.get("run_models", []):
                self.assertIn(model, known, f"{phase['id']} references missing model {model}")

    def test_all_model_inputs_have_a_producer_or_dictionary_entry(self):
        declared = set(KB["data_dictionary"]["paths"])
        produced = set()
        for model in KB["models"].values():
            produced.update(model.get("outputs", []))
        # Some runtime context fields are deliberately external (POI and conflict context).
        external = {"poi", "conflict", "planned_stops_hours", "planned_sleep_hours"}
        missing = []
        for name, model in KB["models"].items():
            for path in (model.get("inputs", []) if isinstance(model.get("inputs", []), list) else [v.get("source_path") for v in model.get("inputs", {}).values() if isinstance(v, dict) and v.get("source_path")]):
                if path not in declared and path not in produced and path.split(".")[0] not in external:
                    missing.append(f"{name}:{path}")
        self.assertEqual(missing, [])

    def test_pack_mode_requires_explicit_declaration(self):
        model = KB["models"]["nutrition_pack_plan"]
        self.assertIn("user.planned_pack_declared", model["inputs"])
        self.assertTrue(any("user.planned_pack_declared=true" in step or "user.planned_pack_declared == true" in step for step in model["algorithm"]["steps"]))
        self.assertIn("planned_pack_declared", WIZARD["defaults_short"]["values"])
        self.assertIs(WIZARD["defaults_short"]["values"]["user.planned_pack_declared"], False)

    def test_one_coverage_safety_application(self):
        for name in ("hydration_carry_plan", "nutrition_pack_plan"):
            formulas = KB["models"][name]["formulas"]
            self.assertNotIn("coverage_safety", formulas["resupply_needed_by_km"].split("*")[:-1])
            # Coverage is already safety-adjusted for hydration; nutrition applies it at resupply.
            if name == "hydration_carry_plan":
                self.assertEqual(formulas["coverage_km_from_start"], "physical_coverage_km * coverage_safety")
                self.assertEqual(formulas["resupply_needed_by_km"], "physical_coverage_km * coverage_safety")
            else:
                self.assertEqual(formulas["coverage_km_from_start"], "coverage_hours * max(user.typical_speed_kmh, 8)")
                self.assertEqual(formulas["resupply_needed_by_km"], "coverage_km_from_start * coverage_safety")

    def test_no_unjustified_decay_reduction_of_fueling_or_fluid(self):
        f = KB["models"]["effort_decay"]["formulas"]
        self.assertIn("stage.cho_target_g_per_h_operational", f["stage.cho_target_g_per_h_adjusted"])
        self.assertNotIn("cho_track_power", f["stage.cho_target_g_per_h_adjusted"])
        self.assertEqual(f["stage.fluid_target_l_per_h_adjusted"], "stage.fluid_target_l_per_h_operational")

    def test_missing_body_mass_is_not_imputed(self):
        formula = KB["models"]["stage_demand"]["formulas"]["relative_effort_factor"]
        self.assertNotIn("75", formula)
        self.assertIn("stage.luggage_effort_component", formula)

    def test_poi_presence_does_not_claim_supply_sufficiency(self):
        for name in ("hydration_carry_plan", "nutrition_pack_plan"):
            formula = KB["models"][name]["formulas"]["satisfied"]
            self.assertIn("false", formula)
            self.assertNotIn("food_poi_chain_ok", formula)
            self.assertNotIn("chain_ok", formula)

    def test_time_margin_uses_real_model_name_and_marks_completeness(self):
        model_names = set(KB["models"])
        p6 = next(p for p in KB["decision_tree"]["phases"] if p["id"] == "P6_refine")
        self.assertIn("time_margin", p6["run_models"])
        self.assertNotIn("time_margin_vs_limit", p6["run_models"])
        self.assertIn("race.margin_completeness", KB["models"]["time_margin"]["outputs"])

class ReferenceMathTests(unittest.TestCase):
    """Reference calculations for the documented equations; not a substitute for PHP integration tests."""
    def test_stage_time_surface_and_elevation(self):
        distance, speed, surface_factor, gain = 60.0, 20.0, 0.88, 300.0
        result = distance / speed / surface_factor + gain / 1000 * 0.15
        self.assertAlmostEqual(result, 3.4540909091, places=6)

    def test_long_stage_cho_is_not_reduced_by_effort_decay(self):
        duration, target = 20.0, 60.0
        self.assertAlmostEqual(duration * target, 1200.0)
        # A falling power factor must not silently reduce the fueling target.
        power_factor_mean = 0.86
        self.assertEqual(target, 60.0)
        self.assertTrue(power_factor_mean < 1.0)

    def test_hydration_resupply_margin_applied_once(self):
        start_l, rate, speed, safety = 1.5, 0.6, 20.0, 0.85
        physical_km = start_l / rate * speed
        latest_resupply_km = physical_km * safety
        self.assertAlmostEqual(physical_km, 50.0)
        self.assertAlmostEqual(latest_resupply_km, 42.5)
        self.assertNotAlmostEqual(latest_resupply_km, physical_km * safety * safety)

    def test_hydration_stage_need_includes_planning_reserve(self):
        rate, hours, reserve = 0.6, 3.0, 0.15
        self.assertAlmostEqual(rate * hours * (1 + reserve), 2.07)

if __name__ == "__main__":
    unittest.main(verbosity=2)
