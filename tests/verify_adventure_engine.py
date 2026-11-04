#!/usr/bin/env python3
"""Verify actual JSON-interpreter output against scenario acceptance criteria."""
import json, argparse
from pathlib import Path
from adventure_engine_runner import execute

def get_path(obj,path):
    cur=obj
    for part in path.split("."):
        if not isinstance(cur,dict) or part not in cur: return None
        cur=cur[part]
    return cur

def verify(kb, scenarios):
    report={"knowledge_version":kb["meta"]["knowledge_version"],"passed":0,"failed":0,"cases":[]}
    for sc in scenarios:
        result=execute(kb,sc); fired=set(result["fired_rule_ids"]); expected=sc.get("expected",{})
        problems=[]
        for rid in expected.get("must_fire",[]):
            if rid not in fired: problems.append(f"Brak wymaganej reguły: {rid}")
        for rid in expected.get("must_not_fire",[]):
            if rid in fired: problems.append(f"Nieoczekiwana reguła: {rid}")
        for rid,severity in expected.get("severity_at_least",{}).items():
            found=next((x for x in result["recommendations"] if x["id"]==rid),None)
            rank={"info":0,"recommendation":1,"warning":2,"critical":3}
            if not found or rank.get(found["severity"],-1)<rank.get(severity,99):
                problems.append(f"{rid}: oczekiwano severity >= {severity}")
        for assertion in sc.get("assertions",[]):
            actual=get_path(result["derived"],assertion["path"])
            op=assertion["op"]; value=assertion.get("value")
            ok={"eq":lambda:actual==value,"gte":lambda:actual is not None and actual>=value,
                "lte":lambda:actual is not None and actual<=value,
                "exists":lambda:actual is not None}.get(op)
            if ok is None: problems.append(f"Nieobsługiwane asercja: {op}")
            elif not ok(): problems.append(f"{assertion['path']}: otrzymano {actual!r}, oczekiwano {op} {value!r}")
        case={"id":sc["id"],"passed":not problems,"problems":problems,
              "fired_rule_ids":result["fired_rule_ids"],
              "key_outputs":{p:get_path(result["derived"],p) for p in [
                  "stage.estimated_time_hours","stage.cho_target_g_per_h_operational",
                  "stage.fluid_target_l_per_h_operational","plan.hydration.status",
                  "plan.nutrition.mode","plan.nutrition.status","plan.gi.risk_band","race.margin_status"]}}
        report["cases"].append(case)
        report["passed"]+=not problems; report["failed"]+=bool(problems)
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--knowledge",default="adventure_knowledge.json")
    p.add_argument("--scenarios",default="tests/scenarios.json")
    p.add_argument("--report",default="tests/verification_report.json")
    a=p.parse_args()
    kb=json.loads(Path(a.knowledge).read_text(encoding="utf-8"))
    scenarios=json.loads(Path(a.scenarios).read_text(encoding="utf-8"))["scenarios"]
    report=verify(kb,scenarios)
    Path(a.report).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"VERIFIER: {report['passed']} passed, {report['failed']} failed / {report['passed']+report['failed']}")
    for c in report["cases"]:
        print(("PASS" if c["passed"] else "FAIL")+f" {c['id']}")
        for issue in c["problems"]: print("  - "+issue)
    if report["failed"]: raise SystemExit(1)
if __name__=="__main__": main()
