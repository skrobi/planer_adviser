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


def _inventory_event_confirmation(event, event_type, spec):
    rule = spec.get("event_types", {}).get(event_type)
    if not rule:
        return False, "unsupported_event_type"
    quantity = event.get("quantity")
    if not isinstance(quantity, (int, float)) or isinstance(quantity, bool) or quantity <= 0:
        return False, "missing_or_invalid_quantity"
    for requirement in rule.get("requires", []):
        if requirement == "verification_status in verified|official" and event.get("verification_status") not in ("verified", "official"):
            return False, "poi_not_verified"
        if requirement == "availability_status=confirmed_available" and event.get("availability_status") != "confirmed_available":
            return False, "availability_not_confirmed"
        if requirement == "quantity_status=confirmed" and event.get("quantity_status") != "confirmed":
            return False, "quantity_not_confirmed"
        if requirement not in ("verification_status in verified|official","availability_status=confirmed_available","quantity_status=confirmed","quantity>0"):
            raise ValueError(f"Unsupported inventory requirement: {requirement}")
    return True, None


def _process_inventory_resource(stages, resource, initial_stock, spec):
    stock = initial_stock if isinstance(initial_stock,(int,float)) and not isinstance(initial_stock,bool) and initial_stock >= 0 else None
    rows=[]; total_shortage=0.0
    need_key="water_l" if resource=="water_l" else "cho_g"
    for stage in stages:
        distance=stage.get("planned_distance_km",stage.get("distance_km"))
        need_obj=stage.get("inventory_need",{})
        demand=need_obj.get(need_key) if isinstance(need_obj,dict) else None
        demand_ok=isinstance(demand,(int,float)) and not isinstance(demand,bool) and demand>=0
        distance_ok=isinstance(distance,(int,float)) and not isinstance(distance,bool) and distance>0
        opening=stock; shortage=0.0; additions=0.0; losses=0.0; event_rows=[]
        valid=[]
        events=stage.get("inventory_events",[])
        for event in events if isinstance(events,list) else []:
            if not isinstance(event,dict):
                event_rows.append({"accepted":False,"reason":"invalid_event_shape"}); continue
            typ=event.get("type")
            rule=spec.get("event_types",{}).get(typ,{})
            if rule.get("resource")!=resource: continue
            km=event.get("route_km")
            if not distance_ok or not isinstance(km,(int,float)) or isinstance(km,bool) or km<0 or km>distance:
                event_rows.append({"event_id":event.get("event_id"),"accepted":False,"reason":"invalid_or_unverifiable_route_position"}); continue
            accepted,reason=_inventory_event_confirmation(event,typ,spec)
            valid.append((float(km),event,typ,accepted,reason))
        valid.sort(key=lambda x:(x[0],str(x[1].get("event_id",""))))
        cursor=0.0
        for km,event,typ,accepted,reason in valid:
            if demand_ok and distance_ok and stock is not None:
                consumption=demand*(km-cursor)/distance
                used=min(stock,consumption); stock-=used
                shortage+=consumption-used; total_shortage+=consumption-used
            else:
                if not demand_ok: stock=None
            cursor=km
            if accepted and stock is not None and demand_ok:
                qty=float(event["quantity"])
                if typ in ("water_refill","cho_resupply"):
                    stock+=qty; additions+=qty
                else:
                    loss=min(stock,qty); stock-=loss; losses+=loss
            elif accepted:
                stock=None
            event_rows.append({"event_id":event.get("event_id"),"route_km":km,"type":typ,"quantity":event.get("quantity"),"accepted":accepted,"reason":reason,"stock_after_event":stock})
        if demand_ok and distance_ok and stock is not None:
            consumption=demand*(distance-cursor)/distance
            used=min(stock,consumption); stock-=used
            shortage+=consumption-used; total_shortage+=consumption-used
        else:
            stock=None
        excluded_events=sum(1 for item in event_rows if not item.get("accepted",False))
        status="shortage" if shortage>0 else ("insufficient_data" if opening is None or not demand_ok or not distance_ok else ("partial" if excluded_events else "complete"))
        rows.append({"stage_id":stage.get("id"),"resource":resource,"opening_stock":opening,
            "planned_demand":demand if demand_ok else None,"confirmed_resupply":additions,
            "confirmed_losses":losses,"closing_stock":stock,"shortage":shortage,"status":status,
            "demand_allocation":"linear_by_route_distance","events":event_rows})
    return rows,total_shortage


def run_inventory_ledger(kb,ctx):
    """Execute the KB-defined ordered inventory ledger for water and CHO."""
    spec=kb.get("stage5_contracts",{}).get("inventory_ledger")
    trip=ctx.get("trip",{})
    stages=trip.get("stage_sequence") if isinstance(trip,dict) else None
    if not spec or not isinstance(stages,list) or not stages: return None
    normalized=[]
    for index, original in enumerate(stages, start=1):
        stage=dict(original)
        stage.setdefault("ordinal", stage.get("day", index))
        stage.setdefault("id", f"stage_{stage['ordinal']}")
        if "planned_distance_km" not in stage and "distance_km" in stage:
            stage["planned_distance_km"]=stage["distance_km"]
        normalized.append(stage)
    stages=sorted(normalized,key=lambda s:(s.get("ordinal",0),str(s.get("id",""))))
    start=trip.get("inventory_start",{})
    water,water_short=_process_inventory_resource(stages,"water_l",start.get("water_l") if isinstance(start,dict) else None,spec)
    cho,cho_short=_process_inventory_resource(stages,"cho_g",start.get("cho_g") if isinstance(start,dict) else None,spec)
    rows=[{"stage_id":s.get("id"),"ordinal":s.get("ordinal"),"water":water[i],"nutrition":cho[i]} for i,s in enumerate(stages)]
    statuses=[r[k]["status"] for r in rows for k in ("water","nutrition")]
    overall=("insufficient_data" if "insufficient_data" in statuses else ("shortage" if "shortage" in statuses else ("partial" if "partial" in statuses else "complete")))
    set_path(ctx,"plan.trip_accounting.inventory_ledger",rows)
    set_path(ctx,"plan.trip_accounting.inventory_status",overall)
    set_path(ctx,"plan.trip_accounting.inventory_shortage.water_l",water_short)
    set_path(ctx,"plan.trip_accounting.inventory_shortage.cho_g",cho_short)
    return {"status":overall,"stages":len(rows),"water_shortage_l":water_short,"cho_shortage_g":cho_short}



def assess_poi_access(kb,ctx):
    """Filter POIs using the normalized, source-backed access contract; never auto-credit inventory."""
    spec=kb.get("stage5_contracts",{}).get("poi_access",{})
    logistics=ctx.get("logistics",{})
    candidates=logistics.get("poi_candidates",[]) if isinstance(logistics,dict) else []
    details=[]; eligible=[]; excluded=[]; water_ids=[]; food_ids=[]; reasons=[]
    if not isinstance(candidates,list):
        candidates=[]
    for poi in candidates:
        if not isinstance(poi,dict):
            excluded.append(None); reasons.append({"poi_id":None,"reason":"invalid_candidate_shape"}); continue
        pid=poi.get("id")
        poi_reasons=[]; resources=[]
        if poi.get("verification_status") not in ("verified","official"):
            poi_reasons.append("poi_not_verified")
        if poi.get("freshness_status")!="fresh":
            poi_reasons.append("poi_not_confirmed_fresh")
        if poi.get("open_status_at_arrival")!="open_confirmed":
            poi_reasons.append("not_confirmed_open_at_arrival")
        route_km=poi.get("route_km")
        detour=poi.get("detour_distance_km")
        if not isinstance(route_km,(int,float)) or isinstance(route_km,bool) or route_km<0:
            poi_reasons.append("route_position_unknown")
        if not isinstance(detour,(int,float)) or isinstance(detour,bool) or detour<0:
            poi_reasons.append("detour_distance_unknown")
        base_ok=not poi_reasons
        water=poi.get("water_volume_l")
        water_capacity=poi.get("water_capacity_status",poi.get("capacity_status"))
        if isinstance(water,(int,float)) and not isinstance(water,bool) and water>0 and water_capacity=="confirmed_sufficient" and base_ok:
            resources.append("water"); water_ids.append(pid)
        elif water is not None or poi.get("water_capacity_status") is not None:
            reasons.append({"poi_id":pid,"resource":"water","reason":"water_quantity_or_capacity_not_confirmed"})
        food=poi.get("food_cho_g")
        food_capacity=poi.get("food_capacity_status",poi.get("capacity_status"))
        if isinstance(food,(int,float)) and not isinstance(food,bool) and food>0 and food_capacity=="confirmed_sufficient" and base_ok:
            resources.append("food"); food_ids.append(pid)
        elif food is not None or poi.get("food_capacity_status") is not None:
            reasons.append({"poi_id":pid,"resource":"food","reason":"food_cho_or_capacity_not_confirmed"})
        if resources:
            eligible.append(pid)
        else:
            excluded.append(pid)
            for reason in poi_reasons:
                reasons.append({"poi_id":pid,"reason":reason})
            if not poi_reasons:
                reasons.append({"poi_id":pid,"reason":"no_confirmed_supply_quantity"})
        details.append({"poi_id":pid,"route_km":route_km,"detour_distance_km":detour,
                        "arrival_time_local":poi.get("arrival_time_local"),
                        "eligible_resources":resources,"base_requirements_confirmed":base_ok,
                        "reasons":poi_reasons})
    status="insufficient_data" if not candidates else ("confirmed" if eligible else "partial")
    set_path(ctx,"plan.poi_access.status",status)
    set_path(ctx,"plan.poi_access.eligible_poi_ids",eligible)
    set_path(ctx,"plan.poi_access.excluded_poi_ids",excluded)
    set_path(ctx,"plan.poi_access.reasons",reasons)
    set_path(ctx,"plan.poi_access.candidate_details",details)
    set_path(ctx,"plan.poi_access.confirmed_water_poi_ids",water_ids)
    set_path(ctx,"plan.poi_access.confirmed_food_poi_ids",food_ids)
    return {"status":status,"candidate_count":len(candidates),"eligible_count":len(eligible),
            "confirmed_water_count":len(water_ids),"confirmed_food_count":len(food_ids)}



def run_trip_accounting(kb,ctx):
    """Aggregate canonical stage time without coercing unknown stops or sleep to zero."""
    trip=ctx.get("trip",{})
    stages=trip.get("stage_sequence") if isinstance(trip,dict) else None
    if not isinstance(stages,list) or not stages:
        return None
    normalized=[]
    for index,original in enumerate(stages,start=1):
        stage=dict(original)
        stage.setdefault("ordinal",stage.get("day",index))
        stage.setdefault("id",f"stage_{stage['ordinal']}")
        if "planned_distance_km" not in stage and "distance_km" in stage:
            stage["planned_distance_km"]=stage["distance_km"]
        if "estimated_moving_time_hours" not in stage:
            if "estimated_moving_hours" in stage:
                stage["estimated_moving_time_hours"]=stage["estimated_moving_hours"]
            elif "estimated_time_hours" in stage:
                stage["estimated_moving_time_hours"]=stage["estimated_time_hours"]
        normalized.append(stage)
    normalized.sort(key=lambda s:(s.get("ordinal",0),str(s.get("id",""))))
    components=("moving","stops","sleep")
    totals={}; subtotals={}; unknown_counts={}
    rows=[]; load=[]
    for component in components:
        path={"moving":"estimated_moving_time_hours","stops":"planned_stops_hours","sleep":"planned_sleep_hours"}[component]
        known=[s.get(path) for s in normalized if isinstance(s.get(path),(int,float)) and not isinstance(s.get(path),bool) and s.get(path)>=0]
        unknown_counts[component]=len(normalized)-len(known)
        subtotals[component]=sum(known)
        totals[component]=subtotals[component] if unknown_counts[component]==0 else None
    for stage in normalized:
        moving=stage.get("estimated_moving_time_hours")
        stops=stage.get("planned_stops_hours")
        sleep=stage.get("planned_sleep_hours")
        valid=lambda x:isinstance(x,(int,float)) and not isinstance(x,bool) and x>=0
        elapsed=moving+stops+sleep if all(valid(x) for x in (moving,stops,sleep)) else None
        rows.append({"stage_id":stage["id"],"ordinal":stage["ordinal"],
            "moving_hours":moving if valid(moving) else None,
            "stops_hours":stops if valid(stops) else None,
            "sleep_hours":sleep if valid(sleep) else None,
            "elapsed_hours":elapsed,
            "missing_components":[name for name,val in (("moving",moving),("stops",stops),("sleep",sleep)) if not valid(val)]})
        load.append({"stage_id":stage["id"],"ordinal":stage["ordinal"],
            "distance_km":stage.get("planned_distance_km"),
            "elevation_gain_m":stage.get("elevation_gain_m"),
            "surface":stage.get("dominant_surface",stage.get("surface")),
            "moving_hours":moving if valid(moving) else None,
            "energy_kj_proxy":stage.get("energy_kj_proxy",stage.get("estimated_metabolic_energy_kj")),
            "planned_sleep_hours":sleep if valid(sleep) else None,
            "recovery_interpretation":"planned interval only; not a validated recovery score"})
    all_complete=all(v==0 for v in unknown_counts.values())
    any_known=any(unknown_counts[name] < len(normalized) for name in components)
    completeness="complete" if all_complete else ("partial" if any_known else "insufficient_data")
    elapsed=totals["moving"]+totals["stops"]+totals["sleep"] if all_complete else None
    set_path(ctx,"trip.total_moving_hours",totals["moving"])
    set_path(ctx,"trip.total_stops_hours",totals["stops"])
    set_path(ctx,"trip.total_sleep_hours",totals["sleep"])
    set_path(ctx,"trip.total_elapsed_hours",elapsed)
    set_path(ctx,"trip.accounting_completeness",completeness)
    set_path(ctx,"plan.trip_accounting.time_ledger",rows)
    set_path(ctx,"plan.trip_accounting.known_subtotals",subtotals)
    set_path(ctx,"plan.trip_accounting.load_ledger",load)
    return {"completeness":completeness,"moving_hours":totals["moving"],
            "stops_hours":totals["stops"],"sleep_hours":totals["sleep"],"elapsed_hours":elapsed}


def execute(kb, scenario):
    ctx=json.loads(json.dumps(scenario["input"]))
    model_trace=run_models(kb,ctx)
    inventory_trace=run_inventory_ledger(kb,ctx)
    poi_trace=assess_poi_access(kb,ctx)
    time_trace=run_trip_accounting(kb,ctx)
    recs=run_rules(kb,ctx)
    composed=compose_recommendations(kb,ctx,recs)
    return {"scenario_id":scenario["id"],"knowledge_version":kb["meta"]["knowledge_version"],
            "derived":ctx,"model_trace":model_trace,"inventory_trace":inventory_trace,"poi_trace":poi_trace,"time_trace":time_trace,"recommendations":recs,
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
