# Formula and pipeline verification report

## Scope
This repository currently contains the knowledge base, wizard definition and illustrative simulation. It does **not** contain the production PHP engine or its formula-DSL evaluator. Therefore these checks validate the knowledge contract and reference equations; they cannot certify that the live Ridemore PHP runtime executes them correctly.

## Corrections made
1. Canonical downstream duration is `stage.estimated_time_hours`, produced by `stage_demand`.
2. Hydration and nutrition coverage safety factor is applied once, not squared.
3. `effort_decay` reports pacing decay only. CHO and fluid targets are passed through unchanged; a power-decay proxy does not justify reducing fueling or hydration.
4. A POI's location alone cannot prove water volume or food/CHO sufficiency. Status can be `satisfied`, `resupply_required` or `insufficient_data`.
5. Body mass is not imputed as 75 kg. The luggage/body component is omitted and completeness is flagged when inputs are missing.
6. Decision tree P6 now invokes the existing `time_margin` model name.
7. Wizard and KB versions and path dictionaries are synchronized; pack mode requires explicit declaration.
8. A very long (>=250 km) single stage with zero planned sleep and beginner experience triggers a critical warning with explicit stop criteria. The 250 km value is an operational review trigger, not a universal physiological boundary.
9. The 5.3 h sleep warning is explicitly an event-specific heuristic, not a safe-sleep threshold; exceeding it does not certify safety.

## Scientific interpretation
- CHO bands are operational planning values, not a universal prescription. The model must consider duration, intensity, practiced tolerance and product type. The evidence supports approximately 30–60 g/h for many 1–2.5 h endurance efforts and higher rates in longer events when tolerated; it does not justify reducing intake solely because an estimated power-decay factor falls.
- Fluid rate defaults are planning estimates only. Individual sweat rate and conditions should take precedence. A single fixed L/h target is not a personal hydration prescription.
- The 15% water reserve and 85% coverage safety factor are operational margins, not clinical thresholds.
- The GI risk score remains a heuristic index, not a clinical probability.

## Automated tests
Run locally with Python 3.11+:
```bash
python -m unittest discover -s tests -v
```
GitHub Actions runs the same suite on pushes to main/fix branches and pull requests.

## Remaining production integration work
- Run the same scenarios through the actual PHP formula DSL and compare outputs with the reference tests.
- Add POI refill volume/food CHO, opening-at-arrival and verification timestamp to the logistics contract.
- Implement explicit missing-data propagation in PHP.
- Add end-to-end tests for wizard hydration, model execution order, expert triggers, suppression and decision trace.

## Scope of version 0.9.3
This pass improves the safety framing and corrects effort-decay outputs. It does not yet resolve the known multi-stage nutrition/hydration accounting, POI capacity/opening-hours contract, or sleep allocation across multiple stages. Those remain a separate integration phase.


## 10. Wizard UX contract – 2026-11-05

The trip wizard is intentionally not a physiology questionnaire. Short mode is the default and has at most eight candidate questions; profile, activity history, route analysis and POI data must be prefilled before rendering. Sweat rate, body mass, GI tolerance, FTP, VO2max and sweat sodium are deferred to a future Advanced Trainer. Manual POI kilometre lists are removed. Unknown luggage mass is no longer replaced with a generic 10 kg assumption.

The fields `ask_if_missing`, `required_when_missing` and `prefill_from` are declarative requirements for the future PHP wizard renderer. The current repository does not yet include that production renderer, so these tests validate the JSON contract rather than live UI behavior.


## 11. Stage 5 – canonical multi-stage and POI contracts (2026-11-05)

The first Stage 5 pass defines contracts, not production calculations. It separates moving time from stops and sleep; establishes ordered shared stage identity; defines trip aggregation completeness; and specifies POI arrival-time, verification, freshness, quantity, capacity and detour requirements. Ridemore remains the owner of POI taxonomy.

A cumulative physiological fatigue score is deliberately not introduced: current inputs and evidence do not justify collapsing distance, ascent, energy proxy, sleep and recovery into one validated scalar. The contract instead requires a transparent per-stage load ledger and explicit inter-stage recovery context.

Multi-stage nutrition/hydration inventory carry-forward is not yet executable. It requires explicit inventory events (start stock, consumption, confirmed purchases/refills, losses and end stock) per stage. The next implementation pass must add this event ledger before claiming trip-level supply sufficiency.

The CI failure on the Stage 4 branch was traced to a missing `meta.question_policy.ask_only_if_missing` key in the wizard metadata. The key is now explicitly declared and covered by a contract test on the Stage 5 branch.

These contracts are not production PHP behavior. PHP execution, real POI adapter mapping, GPX track-segment continuity, and end-to-end tests remain pending.


## 12. Stage 5 branch CI verification (2026-11-05)

GitHub Actions run `41990591353` for PR #3 completed successfully:
- Python unittest suite: **39 tests passed**.
- JSON-driven reference engine: completed successfully.
- Scenario verifier: **10 passed, 0 failed**.
- This verifies the declarative contracts and current Python reference behavior only. It does not verify PHP execution, multi-stage inventory carry-forward, POI opening-time calculations, or real Ridemore adapter integration.


## 13. Multi-stage inventory ledger – reference execution (2026-11-05)

The Python reference interpreter now executes the KB-defined inventory event contract for water and CHO. Initial stock is explicit; missing values remain unknown. Confirmed resupply requires verified/official source, confirmed availability and confirmed positive quantity. Loss events require confirmed positive quantity. Stages carry forward physical remaining stock; route-positioned events are processed in order, and later resupply cannot erase an earlier shortage. Unknown demand or starting stock is never replaced with zero.

For this reference implementation, stage demand is allocated linearly by route distance between events. This is a transparent accounting approximation, not a physiological intake curve. Stage demand must be supplied by stage-level nutrition and hydration models. PHP parity and Ridemore adapter integration remain pending.


## 14. Inventory ledger CI verification (2026-11-05)

The latest PR #3 GitHub Actions run for commit `f1e567733dc2b85645bc798574d0fc36ba2d66ef` completed successfully:
- Python unittest suite: **52 tests passed**.
- Inventory ledger tests: 11 passed, covering stage carry-forward, CHO resupply, verified water refill, closed POI, estimated food quantity, confirmed loss, event ordering, shortage persistence and unknown propagation.
- JSON-driven reference engine and scenario verifier: **10 passed, 0 failed**.

The inventory ledger is now executed by the Python reference interpreter using the event rules in the knowledge base. It is still not production PHP and is not yet connected to live Ridemore POI records. The linear-by-distance demand allocation is an explicit approximation requiring review before production use.


## 15. Canonical stage normalization for inventory

The reference ledger accepts the GPX StagePlanner's current aliases (`day`, `distance_km`) and normalizes them to stable `ordinal`, `id` and `planned_distance_km` fields. The canonical stage contract explicitly requires stage-specific demand from NutritionExpert and HydrationExpert; trip-level demand must not be copied onto every stage.


## 16. POI access assessment – reference implementation

The reference interpreter now evaluates normalized POI candidates separately from inventory events. A POI can be shown as a confirmed water/food option only when source verification, freshness, open-at-arrival status, route position, detour and resource-specific confirmed quantity/capacity are present. Opening-hours parsing and freshness normalization remain Ridemore adapter responsibilities.

A confirmed POI is only a potential resupply option. It does not change inventory automatically; the rider's plan must explicitly select a resupply event. This avoids assuming a purchase or refill that the rider has not selected.


## 17. Final Stage 5 reference verification (2026-11-05)

GitHub Actions run `41991916640` for commit `313b377c5613fd8458838c17f9fb8f995127e9cf` completed successfully:
- Python unittest suite: **54 tests passed**.
- JSON-driven reference engine completed successfully.
- Scenario verifier: **10 passed, 0 failed**.
- Inventory ledger and POI access tests passed.

This confirms the Python reference implementation and declarative contracts only. Production PHP execution, Ridemore POI adapter mapping, and end-to-end parity remain outstanding.


## 18. Trip time accounting – reference implementation

The Python reference interpreter now aggregates moving time, planned stops and planned sleep independently for the full trip. It calculates elapsed time only when all three components are known for every stage. Missing components remain unknown; known subtotals are retained. The load ledger lists per-stage distance, ascent, surface, moving time, energy proxy and planned sleep without producing a cumulative fatigue score.


## 19. Trip time accounting CI verification (2026-11-05)

GitHub Actions run `41992265678` for commit `8d59b10770a249902a403ffa40e81bd95a0f5f4c` completed successfully:
- Python unittest suite: **57 tests passed**.
- JSON-driven reference engine completed successfully.
- Scenario verifier: **10 passed, 0 failed**.
- Inventory, POI access, stage normalization and trip time accounting tests passed.

Time totals keep moving, stops and sleep separate. Complete elapsed time is emitted only when every stage has all three known components; otherwise the elapsed total remains unknown while known subtotals are retained.
