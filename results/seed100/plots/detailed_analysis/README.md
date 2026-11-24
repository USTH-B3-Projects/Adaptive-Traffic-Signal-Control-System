# Seed 100 detailed analysis figures

Reproduction and refresh command (atsc environment):
    python -B scripts/export_seed100_plots.py --refresh

The action replay has already been completed: exactly 12 episodes, using the original saved best policy without training. Do not rerun it to refresh these plots. Its records are isolated under evaluation/seed100/action_audit.

| Figure | Data and display treatment |
| --- | --- |
| 01_learning_curves_reward_and_val.png | Unchanged TensorBoard/NPZ values. Both panels mark the 316800 best checkpoint; validation dip at 172800 is annotated from the actual NPZ mean. Raw training curve and display-only EMA alpha=0.10 retained. |
| 02_tensorboard_losses_and_diagnostics.png | Nine original scalar series. train/value_loss and train/loss use log Y axes with no replacement or clipping of values; the actual 218880 spike is retained. |
| 03_action_decision_and_override_matrix.png | Real audit: requested action by five exclusive interval outcomes, actual KEEP/SWITCH proportions excluding NOOP, and completed green-duration boxplots. Duration comes from controller-boundary timestamps, including automatic substeps, not phase runs times 5 s. |
| 04_timeseries_3600s_all_scenarios.png | Three-seed means at aligned post-step timestamps. Four snapshot rows show raw 5 s values (alpha=0.22, linewidth=0.7) plus full-window trailing 60 s means (12 samples, linewidth=1.8). The smoothed line starts at 60 s; no padded or partial windows. Cumulative arrivals remain unchanged. |
| 05_per_seed_breakdown_101_102_103.png | Preserved byte-for-byte. Individual seed waiting, queue and speed for High/Imbalance and all four methods. |
| 06_ppo_best_vs_final_stability.png | Preserved byte-for-byte. Sample Std ddof=1 and CV across three test seeds. |
| 07_v1_to_v2_progression_comparison.png | Only three independently evaluated models. No 107/500k placeholder; subtitle explains missing evaluation. Historical values and reduction formulas unchanged. Y ceiling increased for label clearance. |

All seven PNG files have 300-DPI metadata and positive size. The existing seed100_baseline_comparison.png remains byte-identical.

## Action audit definitions

- Source: evaluation/seed100/action_audit/action_steps.csv, action_episodes.csv, action_switches.csv.
- Reproducibility: 60/60 episode traffic values match exactly. Arrivals are episode sums; the other four metrics are episode time means. Every 5 s metric/time record also matches the original best evaluation exactly.
- Matrix cells show count and within-requested-action-row percentage. Each decision belongs to one outcome, with max-green override taking priority, then min-green block, transition NOOP, plain KEEP/SWITCH.
- Startup-phase blocks remain executed KEEP and are separately counted; they are not misclassified as min-green blocks.
- Panel B reports percentages over KEEP + SWITCH, explicitly excluding transition NOOP.
- Green durations are measured immediately before an actual green departure. The unfinished last green is right-censored and excluded. Min/max reference lines are 15/75 s.
- Only report Section 3.3 and its related instrumentation paragraph in Section 6.1 were changed. Original evaluation scorecards and all other report text remain unchanged.
- V1 comparisons remain descriptive because timing, seeds and measurement changed. No 500k evaluation or pure inference-latency measurement has been invented.

See quality_checks.json and evaluation/seed100/action_audit/reproducibility_check.json for automated checks.
