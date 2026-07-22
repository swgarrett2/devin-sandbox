# devin-sandbox

## Insurance claim CSV processor

Processes insurance claim data from a CSV file and reports the total approved
claim amount per policy.

Expected CSV columns:

```
claim_id,policy_number,claimant_name,claim_amount,claim_date,status
```

Policy numbers must match the format `AAA-1234567` (three uppercase letters, a
hyphen, then seven digits). Rows with invalid policy numbers or malformed
amounts are skipped and reported instead of being silently included.

### Run

```bash
python process_claims.py                 # uses data/sample_claims.csv
python process_claims.py path/to/file.csv
python process_claims.py path/to/file.csv --strict   # non-zero exit on bad rows
```

### Develop

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy
```
