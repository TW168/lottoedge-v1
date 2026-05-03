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
