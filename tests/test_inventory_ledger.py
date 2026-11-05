import unittest
from adventure_engine_runner import run_inventory_ledger

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
if __name__=="__main__": unittest.main(verbosity=2)
