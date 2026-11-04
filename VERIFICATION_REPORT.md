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
