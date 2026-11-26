# Data

## Where the data comes from

**All three CSVs in `data/` are synthetic.** They were produced by
`scripts/generate_sample_data.py`, which draws random values with Python's
`random` module. They are not UIDAI or data.gov.in data and contain no records
about real people.

| File | Rows | Generator function |
|---|---|---|
| `data/api_data_aadhar_enrolment.csv` | 5,000 | `generate_enrollment_data()` |
| `data/api_data_aadhar_demographic.csv` | 3,000 | `generate_demographic_data()` |
| `data/api_data_aadhar_biometric.csv` | 4,500 | `generate_biometric_data()` |

Row counts were checked with `wc -l data/*.csv` (each file also has one header row).

Things to know about the synthetic data:

- `region_code` and `district` are drawn independently, so they often don't
  match (for example `KA-MYS` next to `Mumbai`). Only `region_code` is used to
  link rows to regions.
- No random seed is set, so running the generator again gives different data
  and different dashboard numbers.
- Dates are relative to the day the generator was run (the last 365 days from
  then), so date-windowed views such as "last 30 days" can come back empty when
  the CSVs are older than that.

Any figure shown by the dashboard describes this synthetic data, not real
Aadhaar activity.

The public demo does not use these files: `scripts/demo_bootstrap.py`
regenerates the same kind of data with a fixed seed (2026) and dates ending
on the day it starts, so "last 30 days" views are not empty. Set
`DEMO_FRESH_DATA=false` to load the committed CSVs instead.

To regenerate (add `--seed N` for repeatable output, `--out DIR` to write
somewhere other than `data/`):

```bash
python scripts/generate_sample_data.py --days 730 --seed 2026
python scripts/setup_complete.py
```

## CSV formats

Column names are lower-cased and trimmed on import. The cleaning code is in
`backend/data_ingestion.py` (`DataIngestionPipeline`).

### Enrolment

```
enrollment_date,gender,age,enrollment_status,aadhaar_generated,region_code,district
2024-09-04,Male,64,Generated,True,MH-PUN,New Delhi
```

- `enrollment_date` is required.
- `gender`: `M`/`F`/`O` and similar spellings are normalised to `Male`/`Female`/`Other`; any other or missing value becomes `Other`.
- `age` is mapped to an age group (`0-18`, `19-35`, `36-60`, `60+`); an
  `age_group` column can be given instead.
- `enrollment_status`: `Pending`, `Verified`, `Rejected` or `Generated`;
  defaults are filled when missing.
- `region_code` is mapped from `district` when absent.

### Demographic updates

```
update_date,update_type,update_status,region_code,district
2024-05-30,Email,Approved,KA-MYS,Mumbai
```

- `update_date` is required.
- `update_type` is normalised to `Name`, `Address`, `Mobile`, `Email`,
  `Biometric`, `Photo` or `DOB`.
- `update_status`: `Pending`, `Approved` or `Rejected`.

### Biometric quality

```
enrollment_date,fingerprint_quality,iris_quality,photo_quality
2025-08-07,76,77,88
```

- Quality scores are clipped to 0–100.
- Rows with a missing or non-numeric score, or an unparseable date, are
  dropped (the count is logged), not filled in.
- **Simulated values:** if a quality column is missing entirely, the cleaning
  code still fills it with random numbers (`np.random.randint`). The upload
  API rejects such files (400), so this only applies to code that calls the
  pipeline directly.
- Rows are linked to enrolment records with the same `enrollment_date`; rows
  with no matching enrolment date are skipped.
- Only quality scores are stored, never biometric images or templates.

## Region codes

| Code | State | District |
|---|---|---|
| MH-MUM | Maharashtra | Mumbai |
| MH-PUN | Maharashtra | Pune |
| MH-NSK | Maharashtra | Nashik |
| KA-BLR | Karnataka | Bengaluru |
| KA-MYS | Karnataka | Mysuru |
| TN-CHN | Tamil Nadu | Chennai |
| TN-CBE | Tamil Nadu | Coimbatore |
| UP-LKO | Uttar Pradesh | Lucknow |
| UP-AGR | Uttar Pradesh | Agra |
| DL-NDL | Delhi | New Delhi |

## Loading your own CSVs

Through the API (needs a login token):

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -d "username=admin&password=<password>" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl -X POST http://localhost:8000/api/import/enrollments/upload \
  -H "Authorization: Bearer $TOKEN" -F "file=@your_enrollments.csv"
```

The other upload routes are `/api/import/demographic/upload` and
`/api/import/biometric/upload`. `GET /api/import/status` returns row counts per table.
