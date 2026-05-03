## System Overview
LottoEdge provides data-driven analysis and pick generation for Texas lottery games.

## Functional Requirements
- Upload CSV history and persist draws.
- Generate picks with statistical and ML signals.
- Support era-aware filtering for games with format changes.

## Non-Functional Requirements
- Prediction inputs must be reproducible and game-rule consistent.
- Data reloads must be idempotent and correction-safe.

## Constraints
- Lottery outcomes remain random; no guarantee of match counts.

## Future Enhancements
- Rename `include_era2` to a generic `include_legacy_eras` API field for clarity.
- Add endpoint-level integration tests for picker payload era toggles.
