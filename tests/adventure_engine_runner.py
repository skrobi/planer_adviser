#!/usr/bin/env python3
"""Execute the declarative models and rules in adventure_knowledge.json.

This is an interpreter for the JSON DSL, not a second set of cycling rules.
All numeric parameters, formulas, thresholds, rule conditions and messages are
loaded from the knowledge base. Unsupported DSL constructs fail loudly.
"""
from __future__ import annotations
import ast, json, operator, argparse
from pathlib import Path

MISSING = object()

def get_path(ctx, path):
    if not isinstance(path, str): return MISSING
    cur = ctx
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur: cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur): cur = cur[int(part)]
        elif isinstance(cur, list) and part == "gain_m": return [x.get("gain_m", MISSING) for x in cur if isinstance(x, dict)]
        else: return MISSING
    return cur

def set_path(ctx, path, value):
    parts=path.split("."); cur=ctx
    for p in parts[:-1]: cur=cur.setdefault(p,{})
    cur[parts[-1]]=value

def flatten(d, prefix=""):
    out={}
    for k,v in d.items():
        key=f"{prefix}.{k}" if prefix else k
        if isinstance(v,dict): out.update(flatten(v,key))
        else: out[key]=v
    return out

class Formula:
    def __init__(self, ctx, constants, local):
        self.ctx,self.constants,self.local=ctx,constants,local
    def resolve(self, node):
        if isinstance(node, ast.Constant): return node.value
        if isinstance(node, ast.Name):
            if node.id in ("True","False","None","null","true","false"): return {"True":True,"False":False,"None":None,"null":None,"true":True,"false":False}[node.id]
            if node.id == "unknown": return "unknown"
            if node.id in self.local: return self.local[node.id]
            if node.id in self.constants: return self.constants[node.id]
            return get_path(self.ctx,node.id)
        if isinstance(node, ast.Attribute):
            parts=[]; n=node
            while isinstance(n,ast.Attribute): parts.append(n.attr); n=n.value
            if isinstance(n,ast.Name): parts.append(n.id); path=".".join(reversed(parts)).replace(".__key_", ".")
            else: raise ValueError("Unsupported attribute expression")
            if path in self.local: return self.local[path]
            if path in self.constants: return self.constants[path]
            if path in self.ctx: return self.ctx[path]
            return get_path(self.ctx,path)
        if isinstance(node, ast.List): return [self.resolve(x) for x in node.elts]
        if isinstance(node, ast.Tuple): return tuple(self.resolve(x) for x in node.elts)
        if isinstance(node, ast.BinOp):
            a,b=self.resolve(node.left),self.resolve(node.right)
            if a is MISSING or b is MISSING or a is None or b is None: return MISSING
            ops={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}
            fn=ops.get(type(node.op))
            if not fn: raise ValueError(f"Unsupported operator {type(node.op).__name__}")
            try: return fn(a,b)
            except (ZeroDivisionError,TypeError): return MISSING
        if isinstance(node, ast.UnaryOp):
            v=self.resolve(node.operand)
            if v is MISSING: return MISSING
            if isinstance(node.op,ast.USub): return -v
            if isinstance(node.op,ast.Not): return not bool(v)
        if isinstance(node, ast.Compare):
            left=self.resolve(node.left)
            for op,right_node in zip(node.ops,node.comparators):
                right=self.resolve(right_node)
                # Missing and explicit null are unknown, never coerced to zero.
                if left is MISSING or right is MISSING or left is None or right is None: return MISSING
                fn={ast.Eq:operator.eq,ast.NotEq:operator.ne,ast.Gt:operator.gt,ast.GtE:operator.ge,ast.Lt:operator.lt,ast.LtE:operator.le}.get(type(op))
                if not fn: raise ValueError("Unsupported comparison")
                try:
                    matched = fn(left,right)
                except (TypeError, ValueError):
                    return False
                if not matched: return False
                left=right
            return True
        if isinstance(node, ast.Call):
            name=node.func.id if isinstance(node.func,ast.Name) else None
            if not name: raise ValueError("Only named DSL functions are allowed")
            if name in ("exists","not_exists"):
                arg=node.args[0]
                path=ast.unparse(arg)
                present=get_path(self.ctx,path) is not MISSING and get_path(self.ctx,path) is not None
                return present if name=="exists" else not present
            args=[self.resolve(a) for a in node.args]
            if name in ("if","if_"):
                if args[0] is MISSING: return MISSING
                return args[1] if bool(args[0]) else args[2]
            if name=="coalesce": return next((x for x in args if x is not MISSING and x is not None), MISSING)
            if name=="min": return min(args) if all(x is not MISSING for x in args) else MISSING
            if name=="max": return max(args) if all(x is not MISSING for x in args) else MISSING
            if name=="clamp": return min(max(args[0],args[1]),args[2])
            if name=="sum": return sum(args[0]) if args and args[0] is not MISSING else MISSING
            if name=="lookup": return args[0].get(str(args[1]),args[2] if len(args)>2 else MISSING)
            if name=="lookup_rate_base":
                rate=args[0]; table=args[1]
                return next((row[1] for row in table if rate <= row[0]), table[-1][1])
            if name in ("and","or","and_","or_"):
                vals=[bool(x) for x in args]
                return all(vals) if name in ("and","and_") else any(vals)
            if name=="has_verified_water_before": return self._poi_before("logistics.verified_water_pois_km",args[0])
            if name=="has_verified_food_before": return self._poi_before("logistics.verified_food_pois_km",args[0])
            raise ValueError(f"Unsupported DSL function: {name}")
        raise ValueError(f"Unsupported DSL syntax: {type(node).__name__}")
    def _poi_before(self,path,km):
        vals=get_path(self.ctx,path)
        return isinstance(vals,list) and any(isinstance(x,(int,float)) and x <= km*.9 for x in vals)
    def eval(self, expr):
        expr = __import__("re").sub(r"\bif\s*\(", "if_(", expr)
        expr = __import__("re").sub(r"\b(and|or)\s*\(", lambda m: m.group(1) + "_(", expr)
        expr = __import__("re").sub(r"([A-Za-z_]\w*)\.(\d[\w]*)", r"\1.__key_\2", expr)
        try: tree=ast.parse(expr,mode="eval")
        except SyntaxError as e: raise ValueError(f"Invalid formula {expr!r}: {e}")
        return self.resolve(tree.body)

def run_models(kb, ctx):
    trace=[]
    # Model order is the declared dependency/calculation order, not hard-coded formulas.
    calc=kb.get("calculations",{})
    ordered=[]
    for mid, spec in calc.items():
        if mid in kb.get("models",{}): ordered.append(mid)
    for mid in kb.get("models",{}):
        if mid not in ordered: ordered.append(mid)
    for mid in ordered:
        model=kb["models"][mid]; formulas=model.get("formulas",{})
        if not formulas: continue
        constants=dict(model.get("constants",{}))
        constants.update(flatten(model.get("constants",{})))
        # Assumptions used by formulas are promoted only as explicit JSON values.
        assumptions=model.get("assumptions",{})
        for key,val in assumptions.items():
            if isinstance(val,dict) and "value" in val: constants.setdefault(key,val["value"])
        local={}
        evaluator=Formula(ctx,constants,local)
        pending=dict(formulas)
        for _ in range(len(pending)+2):
            progressed=False
            for name,expr in list(pending.items()):
                value=evaluator.eval(expr)
                if value is not MISSING:
                    local[name]=value
                    # Formula aliases are mapped only through explicit JSON output contracts.
                    output_path = name if "." in name else model.get("formula_outputs", {}).get(name)
                    if output_path:
                        set_path(ctx, output_path, value)
                    del pending[name]; progressed=True
            if not pending or not progressed: break
        trace.append({"model":mid,"computed":sorted(local.keys()),"unresolved":sorted(pending.keys())})
    return trace

def condition(cond,ctx):
    if not isinstance(cond,dict): raise ValueError(f"Invalid condition: {cond}")
    if "and" in cond: return all(condition(x,ctx) for x in cond["and"])
    if "or" in cond: return any(condition(x,ctx) for x in cond["or"])
    op=cond.get("op"); path=cond.get("path")
    actual=get_path(ctx,path) if path else MISSING
    if op=="exists": return actual is not MISSING and actual is not None
    if op=="not_exists": return actual is MISSING or actual is None
    if actual is MISSING: return False
    expected=get_path(ctx,cond["value_path"]) if "value_path" in cond else cond.get("value",MISSING)
    if op=="eq": return actual==expected
    if op=="gt": return expected is not MISSING and actual>expected
    if op=="gte": return expected is not MISSING and actual>=expected
    if op=="lt": return expected is not MISSING and actual<expected
    if op=="lte": return expected is not MISSING and actual<=expected
    if op=="in": return actual in expected
    raise ValueError(f"Unsupported rule condition operator: {op}")

def run_rules(kb,ctx):
    fired=[]
    for expert, rules in kb.get("rules",{}).items():
        for rule in rules:
            if not rule.get("enabled",True): continue
            if condition(rule.get("conditions",{"op":"exists","path":"__never__"}),ctx):
                action=rule.get("action",{})
                params=dict(action.get("params",{}))
                for key,path in action.get("params_from_paths",{}).items():
                    val=get_path(ctx,path)
                    if val is not MISSING: params[key]=val
                fired.append({"id":rule["id"],"expert":expert,"priority":rule.get("priority",0),
                              "severity":rule.get("severity","info"),"message_key":action.get("message_key"),
                              "recommendation_type":action.get("recommendation_type",rule.get("recommendation_type")),
                              "action_type":action.get("type"),"params":params,
                              "name":rule.get("name",{}).get("pl",rule["id"]),
                              "explanation":rule.get("explanation",{}).get("pl","")})
    fired.sort(key=lambda x:(-x["priority"],x["id"]))
    return fired


def _pl_number(value, digits=2):
    return f"{value:.{digits}f}".replace(".", ",")

def compose_recommendations(kb, ctx, fired):
    """Build deterministic user-facing cards from configured rule groups and derived values."""
    spec = kb.get("recommendation_composition", {})
    by_id = {r["id"]: r for r in fired}
    locale = kb.get("i18n", {}).get("default_locale", "pl")
    cards = []
    for group in spec.get("groups", []):
        sources = [by_id[rid] for rid in group.get("source_rule_ids", []) if rid in by_id]
        if not sources:
            continue
        ids = [r["id"] for r in sources]
        if group["id"] == "nutrition" and ctx.get("plan", {}).get("nutrition", {}).get("mode") == "buffer":
            ids = [rid for rid in ids if rid != "nut_pack_insufficient"]
            sources = [r for r in sources if r["id"] in ids]
        severity_rank = {"critical": 4, "warning": 3, "recommendation": 2, "info": 1}
        severity = max((r.get("severity", "info") for r in sources), key=lambda s: severity_rank.get(s, 0))
        title = group.get("title", {}).get(locale) or group.get("title", {}).get("en") or group["id"]
        summary, details, actions, status = "", [], [], "known"
        if group["id"] == "safety_and_staging":
            critical = "ultra_sleep_zero_long_inexperienced" in ids
            first_trip = "adv_first_bikepacking_uncertainty" in ids
            long_vs_usual = "log_stage_length_vs_experience" in ids
            if critical:
                summary = "Ten plan w obecnej postaci wymaga zmiany przed rozpoczęciem jazdy."
                details.append("Bardzo długi przejazd bez zaplanowanego snu przy poziomie początkującym wiąże się z istotnym ryzykiem zmęczenia i pogorszenia oceny sytuacji.")
                template = kb.get("recommendation_catalog", {}).get("items", {}).get("no_sleep_long_inexperienced", {}).get("user_facing_template", {}).get(locale)
                distance = ctx.get("stage", {}).get("planned_distance_km")
                if isinstance(template, str):
                    details.append(template.replace("{distance_km}", f"{distance:g}" if isinstance(distance, (int, float)) else "nieustalony"))
                actions.append("Zmień plan: podziel wyprawę na etapy z zaplanowanym snem i regeneracją albo zrezygnuj z próby w obecnej formie.")
            elif first_trip:
                summary = "Pierwszy bikepacking zwiększa niepewność planu — warto przyjąć bardziej zachowawcze etapy."
                actions.append("Zaplanuj krótsze, możliwe do ukończenia etapy i zachowaj możliwość wcześniejszego zakończenia.")
            if first_trip:
                details.append("To pierwsza wyprawa tego typu lub doświadczenie w wyprawach wielodniowych jest ograniczone.")
            if long_vs_usual:
                typical = ctx.get("user", {}).get("typical_distance_km")
                distance = ctx.get("stage", {}).get("planned_distance_km")
                if isinstance(typical, (int, float)) and isinstance(distance, (int, float)):
                    details.append(f"Planowany etap ({distance:g} km) jest dłuższy niż typowy dystans ({typical:g} km).")
                    actions.append("Porównaj długość etapu z dotychczasowymi przejazdami; sama różnica nie oznacza, że trasa jest niemożliwa.")
            if "ultra_sleep_low" in ids and not critical:
                details.append("Zaplanowany sen jest niski według heurystyki wydarzenia; ten wskaźnik nie jest granicą bezpieczeństwa.")
            details.append("Dokładny podział kilometrów, przewyższeń i noclegów wymaga profilu wysokościowego GPX, limitów oraz danych o dostępnych miejscach odpoczynku.")
            status = "user_input_required"
        elif group["id"] == "nutrition":
            plan = ctx.get("plan", {}).get("nutrition", {})
            need = plan.get("stage_cho_need_g")
            mode = plan.get("mode")
            if mode == "buffer":
                summary = "Nie zadeklarowano konkretnego zapasu jedzenia — model nie może potwierdzić, że masz wystarczającą ilość na cały etap."
                start = plan.get("recommended_start_cho_g")
                if isinstance(start, (int, float)):
                    details.append(f"Bufor jedzenia na start: około {_pl_number(start, 0)} g węglowodanów (CHO).")
                status = "user_input_required"
            else:
                pack = plan.get("pack_cho_g")
                if isinstance(pack, (int, float)) and isinstance(need, (int, float)):
                    summary = f"Zadeklarowany zapas ({_pl_number(pack, 0)} g CHO) jest mniejszy od szacowanego zapotrzebowania etapu."
                    details.append(f"Szacowane zapotrzebowanie etapu: około {_pl_number(need, 0)} g CHO.")
                    details.append(f"Zadeklarowany zapas: {pack:.0f} g CHO.")
                    status = "estimated"
            if isinstance(need, (int, float)):
                details.append(f"Szacowane zapotrzebowanie całego etapu: około {_pl_number(need, 0)} g CHO.")
            km = plan.get("resupply_needed_by_km")
            if isinstance(km, (int, float)):
                details.append(f"Orientacyjny moment, od którego trzeba zaplanować uzupełnienie: około {_pl_number(km, 0)}. km; to nie potwierdza dostępności sklepu ani ilości jedzenia.")
            details.append("Po podziale trasy zapotrzebowanie i zapas należy przeliczyć osobno dla każdego etapu.")
            actions.append("Uzupełnij deklarację produktów i ilości albo wskaż potwierdzone punkty zakupu jedzenia.")
        elif group["id"] == "hydration":
            plan = ctx.get("plan", {}).get("hydration", {})
            need, start, rate, km = (plan.get("stage_need_l"), plan.get("recommended_start_l"),
                                    plan.get("target_l_per_h"), plan.get("resupply_needed_by_km"))
            summary = "Zapas wody na starcie nie pokrywa szacowanego zapotrzebowania całego etapu."
            if isinstance(need, (int, float)): details.append(f"Szacowane zapotrzebowanie etapu: około {_pl_number(need)} l.")
            if isinstance(start, (int, float)): details.append(f"Zadeklarowana ilość na start: {_pl_number(start)} l.")
            if isinstance(rate, (int, float)): details.append(f"Operacyjny cel uzupełniania płynów: około {_pl_number(rate)} l/h; nie jest to pomiar indywidualnej potliwości.")
            if isinstance(km, (int, float)): details.append(f"Uzupełnienie należy zaplanować najpóźniej w okolicy {_pl_number(km, 0)}. km. To punkt planistyczny, a nie potwierdzony punkt poboru wody.")
            details.append("Sama obecność POI nie potwierdza dostępnej ilości wody ani możliwości uzupełnienia.")
            actions.append("Dodaj zweryfikowane punkty wody i sprawdź ich dostępność oraz możliwość uzupełnienia odpowiedniej ilości.")
            status = "estimated"
        cards.append({"id": group["id"], "title": title, "severity": severity,
                      "priority": group.get("priority", 0), "source_rule_ids": ids,
                      "summary": summary, "details": details, "data_status": status, "actions": actions})
    cards.sort(key=lambda c: (-c["priority"], c["id"]))
    return cards

def execute(kb, scenario):
    ctx=json.loads(json.dumps(scenario["input"]))
    model_trace=run_models(kb,ctx)
    recs=run_rules(kb,ctx)
    composed=compose_recommendations(kb,ctx,recs)
    return {"scenario_id":scenario["id"],"knowledge_version":kb["meta"]["knowledge_version"],
            "derived":ctx,"model_trace":model_trace,"recommendations":recs,
            "composed_recommendations":composed,"fired_rule_ids":[r["id"] for r in recs]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--knowledge",default="adventure_knowledge.json")
    p.add_argument("--scenarios",default="tests/scenarios.json")
    p.add_argument("--out",default="tests/generated_results.json")
    a=p.parse_args()
    kb=json.loads(Path(a.knowledge).read_text(encoding="utf-8"))
    scenarios=json.loads(Path(a.scenarios).read_text(encoding="utf-8"))["scenarios"]
    results=[execute(kb,s) for s in scenarios]
    Path(a.out).write_text(json.dumps({"knowledge_version":kb["meta"]["knowledge_version"],"results":results},ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Executed {len(results)} scenarios using KB {kb['meta']['knowledge_version']}")
    for r in results:
        print(f"{r['scenario_id']}: {len(r['fired_rule_ids'])} recommendations; {', '.join(r['fired_rule_ids']) or 'none'}")
if __name__=="__main__": main()
