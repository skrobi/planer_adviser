import unittest
import json
from pathlib import Path
from adventure_engine_runner import run_inventory_ledger

ROOT=Path(__file__).resolve().parents[1]
REAL_KB=json.loads((ROOT / "adventure_knowledge.json").read_text(encoding="utf-8"))

KB={"stage5_contracts":{"inventory_ledger":{"event_types":{
"water_refill":{"resource":"water_l","requires":["verification_status in verified|official","availability_status=confirmed_available","quantity_status=confirmed","quantity>0"]},
"cho_resupply":{"resource":"cho_g","requires":["verification_status in verified|official","availability_status=confirmed_available","quantity_status=confirmed","quantity>0"]},
"water_loss":{"resource":"water_l","requires":["quantity_status=confirmed","quantity>0"]},
"cho_loss":{"resource":"cho_g","requires":["quantity_status=confirmed","quantity>0"]}
}}}}

def refill(eid,km,qty,verification="verified",availability="confirmed_available",qstatus="confirmed"):
 return {"event_id":eid,"type":"water_refill","route_km":km,"quantity":qty,"verification_status":verification,"availability_status":availability,"quantity_status":qstatus}

def context(stages,water=2.0,cho=200.0):
 return {"trip":{"inventory_start":{"water_l":water,"cho_g":cho},"stage_sequence":stages}}

class InventoryLedgerTests(unittest.TestCase):

 def test_reference_interpreter_uses_real_knowledge_base_config(self):
  c=context([{"id":"a","ordinal":1,"planned_distance_km":100,"inventory_need":{"water_l":1,"cho_g":100},"inventory_events":[refill("poi",50,1)]}],water=1,cho=100)
  run_inventory_ledger(REAL_KB,c)
  row=c["plan"]["trip_accounting"]["inventory_ledger"][0]["water"]
  self.assertEqual(row["confirmed_resupply"],1)
  self.assertEqual(row["closing_stock"],1)

 def test_stock_carries_forward(self):
  c=context([{"id":"a","ordinal":1,"planned_distance_km":50,"inventory_need":{"water_l":1,"cho_g":100}},{"id":"b","ordinal":2,"planned_distance_km":50,"inventory_need":{"water_l":1,"cho_g":100}}])
  run_inventory_ledger(KB,c); rows=c["plan"]["trip_accounting"]["inventory_ledger"]
  self.assertEqual(rows[0]["water"]["closing_stock"],1)
  self.assertEqual(rows[1]["water"]["opening_stock"],1)
  self.assertEqual(rows[1]["water"]["closing_stock"],0)
  self.assertEqual(c["plan"]["trip_accounting"]["inventory_status"],"complete")
 def test_unverified_resupply_is_not_credited(self):
  c=context([{"id":"a","ordinal":1,"planned_distance_km":100,"inventory_need":{"water_l":3,"cho_g":100},"inventory_events":[refill("x",50,5,verification="unverified")]}],water=1)
  run_inventory_ledger(KB,c); row=c["plan"]["trip_accounting"]["inventory_ledger"][0]["water"]
  self.assertEqual(row["confirmed_resupply"],0); self.assertEqual(row["shortage"],2)
  self.assertEqual(row["events"][0]["reason"],"poi_not_verified")
 def test_late_resupply_does_not_erase_earlier_shortage(self):
  c=context([{"id":"a","ordinal":1,"planned_distance_km":100,"inventory_need":{"water_l":4,"cho_g":100},"inventory_events":[refill("late",75,5)]}],water=1)
  run_inventory_ledger(KB,c); row=c["plan"]["trip_accounting"]["inventory_ledger"][0]["water"]
  self.assertEqual(row["shortage"],2); self.assertEqual(row["closing_stock"],4); self.assertEqual(row["status"],"shortage")
 def test_unknown_values_are_not_zero(self):
  c=context([{"id":"a","ordinal":1,"planned_distance_km":100,"inventory_need":{"water_l":None,"cho_g":100}}],water=None)
  run_inventory_ledger(KB,c); row=c["plan"]["trip_accounting"]["inventory_ledger"][0]["water"]
  self.assertIsNone(row["opening_stock"]); self.assertIsNone(row["closing_stock"])
  self.assertEqual(c["plan"]["trip_accounting"]["inventory_status"],"insufficient_data")
 def test_confirmed_refill_at_stage_start(self):
  c=context([{"id":"a","ordinal":1,"planned_distance_km":100,"inventory_need":{"water_l":3,"cho_g":100},"inventory_events":[refill("start",0,3)]}],water=0)
  run_inventory_ledger(KB,c); row=c["plan"]["trip_accounting"]["inventory_ledger"][0]["water"]
  self.assertEqual(row["confirmed_resupply"],3); self.assertEqual(row["closing_stock"],0)

 def test_cho_resupply_is_carried_forward(self):
  c=context([{"id":"a","ordinal":1,"planned_distance_km":100,"inventory_need":{"water_l":1,"cho_g":150},"inventory_events":[{"event_id":"food","type":"cho_resupply","route_km":50,"quantity":100,"verification_status":"official","availability_status":"confirmed_available","quantity_status":"confirmed"}]}],water=2,cho=100)
  run_inventory_ledger(KB,c); row=c["plan"]["trip_accounting"]["inventory_ledger"][0]["nutrition"]
  self.assertEqual(row["confirmed_resupply"],100); self.assertEqual(row["closing_stock"],50)
 def test_unconfirmed_food_quantity_is_not_credited(self):
  c=context([{"id":"a","ordinal":1,"planned_distance_km":100,"inventory_need":{"water_l":1,"cho_g":150},"inventory_events":[{"event_id":"food","type":"cho_resupply","route_km":10,"quantity":200,"verification_status":"verified","availability_status":"confirmed_available","quantity_status":"estimated"}]}],water=2,cho=100)
  run_inventory_ledger(KB,c); row=c["plan"]["trip_accounting"]["inventory_ledger"][0]["nutrition"]
  self.assertEqual(row["confirmed_resupply"],0); self.assertEqual(row["shortage"],50); self.assertEqual(row["events"][0]["reason"],"quantity_not_confirmed")
 def test_closed_poi_does_not_add_water(self):
  c=context([{"id":"a","ordinal":1,"planned_distance_km":100,"inventory_need":{"water_l":3,"cho_g":100},"inventory_events":[refill("closed",10,5,availability="closed")]}],water=1)
  run_inventory_ledger(KB,c); row=c["plan"]["trip_accounting"]["inventory_ledger"][0]["water"]
  self.assertEqual(row["confirmed_resupply"],0); self.assertEqual(row["events"][0]["reason"],"availability_not_confirmed")
 def test_confirmed_loss_reduces_stock(self):
  c=context([{"id":"a","ordinal":1,"planned_distance_km":100,"inventory_need":{"water_l":1,"cho_g":100},"inventory_events":[{"event_id":"spill","type":"water_loss","route_km":20,"quantity":0.5,"quantity_status":"confirmed"}]}],water=2)
  run_inventory_ledger(KB,c); row=c["plan"]["trip_accounting"]["inventory_ledger"][0]["water"]
  self.assertEqual(row["confirmed_losses"],0.5); self.assertEqual(row["closing_stock"],0.5)
 def test_excluded_event_marks_ledger_partial_when_no_shortage(self):
  c=context([{"id":"a","ordinal":1,"planned_distance_km":100,"inventory_need":{"water_l":1,"cho_g":100},"inventory_events":[refill("unknown",50,3,availability="unknown")]}],water=2)
  run_inventory_ledger(KB,c); row=c["plan"]["trip_accounting"]["inventory_ledger"][0]["water"]
  self.assertEqual(row["status"],"partial"); self.assertEqual(c["plan"]["trip_accounting"]["inventory_status"],"partial")

if __name__=="__main__": unittest.main(verbosity=2)
