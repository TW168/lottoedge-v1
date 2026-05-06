# Architecture Notes

## 2026-05-03 Prediction Reliability Fixes

### Data ingestion and retrieval
- `app/services/data_loader.py` now updates existing draw rows when a CSV re-upload contains corrected values for an existing `game + draw_date`.
- Upsert now returns explicit counters: inserted rows and updated rows.
- Default era filtering behavior is now game-aware:
  - Texas Lotto: Era 2 is excluded by default unless `include_era2=true`.
  - Powerball: only Era 3 (current 5/69 + PB/26 format) is included by default unless `include_era2=true`.

### Pick generation validation
- `app/services/pick_generator.py` now enforces group-span and consecutive rules as hard validation failures, instead of advisory notes only.
- Pick generation now uses anti-repeat controls:
  - Adaptive candidate pool size grows with requested diversity and ticket count.
  - Per-run number usage caps prevent sticky anchor numbers from dominating a batch.
  - Bonus-ball selection now applies run-level and recent-history penalties.
- Texas Two Step display scores are calibrated from raw composite scores to a clearer 70-90 confidence band while preserving pick ordering. Raw values are retained as `raw_composite_score` in API output.

### Generated pick memory
- `app/services/pick_history.py` stores recent generated picks in `data/pick_history.json`.
- Recent usage snapshots are fed back into generation as recency penalties, reducing repeat outputs across repeated API calls.

### UI behavior
- `app/templates/picks.html` and `app/static/js/picks.js` include a legacy-era toggle used by pick generation requests.
- Toggle label changes by game to explain what legacy inclusion means for Lotto vs Powerball.
