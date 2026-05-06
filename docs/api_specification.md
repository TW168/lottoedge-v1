# API Specification

## POST /api/upload/{game}

Endpoint Purpose: Upload game CSV, parse rows, and upsert draw history.
Method: POST
Route: `/api/upload/{game}`
Request Body / Params:
- `game` path param: `cash5 | lotto | twostep | powerball`
- multipart form-data file field: `file`

Example Response:
```json
{
  "game": "powerball",
  "rows_parsed": 1200,
  "rows_inserted": 2,
  "rows_updated": 1,
  "total_rows": 1200
}
```

Notes:
- `rows_updated` is returned when uploaded rows match an existing draw date and existing DB values are corrected.

## POST /api/picks/generate

Endpoint Purpose: Generate optimized picks from stored draw history.
Method: POST
Route: `/api/picks/generate`

Request Body / Params (excerpt):
- `game`: `lotto | twostep | powerball`
- `count`: number of generated picks
- `include_era2`: legacy-era inclusion toggle

Behavior:
- For Lotto, `include_era2=false` excludes era2 rows.
- For Powerball, `include_era2=false` restricts prediction data to era3 rows only.
- Saved exclusions are automatically filtered out from generated picks.

## GET /api/picks/exclusions

Endpoint Purpose: Retrieve all persisted played combinations excluded from future predictions.
Method: GET
Route: `/api/picks/exclusions`

Example Response:
```json
{
  "cash5": {
    "main": [[4, 6, 16, 21, 31]]
  },
  "twostep": {
    "main": [],
    "with_bonus": [{"numbers": [1, 17, 20, 25], "bonus": 35}]
  }
}
```

## POST /api/picks/exclusions

Endpoint Purpose: Save one played combination so it is never returned by prediction endpoints.
Method: POST
Route: `/api/picks/exclusions`

Request Body / Params:
- `game`: `lotto | cash5 | twostep | powerball`
- `numbers`: sorted or unsorted main numbers (must match game pick size)
- `bonus` (required only for `twostep` and `powerball`)

Example Request:
```json
{
  "game": "powerball",
  "numbers": [6, 36, 47, 52, 64],
  "bonus": 20
}
```

## POST /api/picks/exclusions/batch

Endpoint Purpose: Save multiple played combinations in one request.
Method: POST
Route: `/api/picks/exclusions/batch`

Request Body / Params:
- `picks`: array of exclusion objects matching POST `/api/picks/exclusions` body format.

Behavior:
- Duplicate entries are ignored (idempotent insert behavior).
- Cash Five ensemble predictions and pick-generation endpoint both honor this exclusion list.
