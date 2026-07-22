# devin-sandbox

## Home insurance quote API (Node.js / Express)

A minimal Express API exposing `POST /api/quotes` for home insurance quote
requests. It was built as a security exercise: the first commit intentionally
ships a basic input-validation vulnerability (flagged by `eslint-plugin-security`)
and a follow-up commit fixes it with `zod` schema validation.

```bash
npm install
npm start                # starts the API on PORT (default 3000)
npm run lint:security    # eslint + eslint-plugin-security
npm run audit            # npm audit
```

See [`SECURITY_NOTES.md`](./SECURITY_NOTES.md) for the endpoint contract, the
intentional vulnerability, the before/after lint output, and what was fixed.

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
