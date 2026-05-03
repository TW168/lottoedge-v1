# Database Schema Notes

## draws table behavior update (2026-05-03)

`draws` rows are uniquely constrained by `(game, draw_date)`.

Upsert policy:
- If `(game, draw_date)` does not exist: insert row.
- If `(game, draw_date)` exists and values differ: update row fields (`n1..n6`, `bonus`, `power_play`, `era`, `is_bonus_era`).
- If identical: no-op.

This supports corrected historical files without duplicate rows.
