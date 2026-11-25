# Test fixtures

Tiny hand-written CSVs used by `tests/integration/test_import.py`. Synthetic;
keep every file well under 1 MB.

| File | Used to check |
|---|---|
| `enrolment_valid.csv` | A valid enrolment upload adds 3 rows with these dates |
| `enrolment_missing_gender.csv` | 400 naming the missing `gender` column |
| `biometric_missing_scores.csv` | 400 listing the missing biometric score columns |
