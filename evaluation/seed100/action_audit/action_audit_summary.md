# Seed 100 best-model action audit

Exactly 12 deterministic replays: seeds 101,102,103 by low,medium,high,imbalance.
No training and no original evaluation modification. CUDA model prediction; original environment/controller.

- Decision records: 8640
- Episode traffic checks: 60/60 exact float equality; max absolute difference 0.
- Step/time checks: 51840 exact equalities (720 samples × 12 × 6 fields).
- Completed green intervals: 1516

| Outcome | Count | Fraction of all decisions (%) |
| --- | --- | --- |
| KEEP | 3452 | 39.953704 |
| SWITCH | 1427 | 16.516204 |
| transition_noop | 1515 | 17.534722 |
| blocked_min_green | 2157 | 24.965278 |
| forced_max_green | 89 | 1.030093 |

Matrix categories are exclusive: max-green override, min-green block, transition NOOP, plain KEEP/SWITCH.
Startup-phase overrides, if any, remain KEEP and are separately counted; they are not relabelled min-green.
Panel B excludes NOOP from the KEEP/SWITCH denominator; panel A includes every decision.
Panel C uses pre-transition green_elapsed observed at the actual controller _next boundary, including automatic substeps.
No duration is inferred as phase runs × 5 s. Unfinished green at episode end is right-censored and excluded.
Runtime wrappers only record calls and delegate unchanged to original bound controller methods.
action_steps.csv retains pre/post state, request-time execution, interval execution and exact transition JSON.
action_switches.csv contains every completed green interval. Arrivals remain episode SUM, other metrics remain time means.

Protected-input hashes and report-region hashes are in preservation_manifest.json.
Detailed exact traffic checks are in reproducibility_check.json.
