# Development Guidelines

## Regression Guardrails Added (2026-05-03)

- Ensure Powerball default predictions run on Era 3 only unless legacy eras are explicitly included.
- Treat group-span and consecutive constraints as enforced validation in pick generation.
- CSV upload reprocessing must support correcting existing draw dates (update instead of skip).
- Any future changes to upload responses must keep frontend upload status messaging in sync.

## Tests Added

- `tests/test_data_loader.py`
  - verifies upsert updates existing draw rows
  - verifies Powerball default era filtering
- `tests/test_pick_generator.py`
  - verifies group and consecutive failures are enforced
