import unittest
from pathlib import Path

from route_stage_planner import analyze_points, parse_gpx, plan_stages

ROOT = Path(__file__).resolve().parents[1]
GPX = ROOT / "tests" / "kotlina400-bikepacking-route.gpx"


class RouteStagePlannerTests(unittest.TestCase):
    def test_synthetic_route_is_analyzed_and_split_into_requested_days(self):
        points = [
            {"lat": 50.0, "lon": 19.0, "ele_m": 300},
            {"lat": 50.0045, "lon": 19.0, "ele_m": 400},
            {"lat": 50.0090, "lon": 19.0, "ele_m": 500},
            {"lat": 50.0135, "lon": 19.0, "ele_m": 450},
            {"lat": 50.0180, "lon": 19.0, "ele_m": 350},
        ]
        route = analyze_points(points, bin_m=250, median_radius=1, smooth_radius=1)
        result = plan_stages(
            route,
            {"body_mass_kg": 75, "bike_mass_kg": 14, "luggage_mass_kg": 8,
             "typical_speed_kmh": 20},
            {"days": 2, "max_riding_hours_per_day": 8},
        )
        self.assertEqual(len(result["stages"]), 2)
        self.assertAlmostEqual(sum(s["distance_km"] for s in result["stages"]),
                               route["distance_km"], places=5)
        self.assertTrue(all(s["estimated_metabolic_energy_kcal"] > 0 for s in result["stages"]))
        self.assertTrue(all(s["end_coordinate"] for s in result["stages"]))

    def test_kotlina400_real_gpx_has_requested_four_stages(self):
        route = analyze_points(parse_gpx(GPX))
        result = plan_stages(
            route,
            {"body_mass_kg": 75, "bike_mass_kg": 14, "luggage_mass_kg": 8,
             "typical_speed_kmh": 18, "gross_efficiency": 0.22},
            {"days": 4, "max_riding_hours_per_day": 12},
        )
        self.assertGreater(route["distance_km"], 400)
        self.assertEqual(len(result["stages"]), 4)
        self.assertAlmostEqual(sum(s["distance_km"] for s in result["stages"]),
                               route["distance_km"], places=4)
        self.assertAlmostEqual(sum(s["elevation_gain_m"] for s in result["stages"]),
                               route["smoothed_elevation_gain_m"], places=2)
        self.assertTrue(all(s["estimated_moving_hours"] > 0 for s in result["stages"]))
        self.assertTrue(all(s["mechanical_work_kj"] > 0 for s in result["stages"]))

    def test_daily_time_limit_is_reported_without_changing_user_day_count(self):
        points = [{"lat": 50, "lon": 19, "ele_m": 100},
                  {"lat": 50.045, "lon": 19, "ele_m": 500},
                  {"lat": 50.09, "lon": 19, "ele_m": 100}]
        route = analyze_points(points, bin_m=250)
        result = plan_stages(route,
            {"body_mass_kg": 80, "typical_speed_kmh": 12},
            {"days": 2, "max_riding_hours_per_day": 0.01})
        self.assertEqual(len(result["stages"]), 2)
        self.assertTrue(any(s["load_status"] == "over_user_time_limit" for s in result["stages"]))


if __name__ == "__main__":
    unittest.main()
