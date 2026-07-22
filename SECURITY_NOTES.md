# Home insurance quote API — security notes

## What the endpoint does

`POST /api/quotes` accepts a home insurance quote request and returns an
estimated annual premium.

Request body:

| Field              | Type   | Notes                                             |
| ------------------ | ------ | ------------------------------------------------- |
| `applicantName`    | string | 1–100 chars                                       |
| `email`            | string | valid email, ≤254 chars                           |
| `propertyAddress`  | string | 1–200 chars                                       |
| `propertyValue`    | number | positive, finite, ≤1,000,000,000                  |
| `yearBuilt`        | number | integer, 1800–current year                        |
| `constructionType` | string | one of `frame`, `masonry`, `fire-resistive`       |

The premium is `(propertyValue / 1000) * rate * ageFactor`, where `rate` comes
from a per-construction-type table and `ageFactor = 1 + (currentYear - yearBuilt) / 100`.

There is also a `GET /health` liveness endpoint.

## How to run

```bash
npm install
npm start                     # starts on PORT (default 3000)

# valid request -> 200 with a quote
curl -s -X POST http://localhost:3000/api/quotes \
  -H 'Content-Type: application/json' \
  -d '{"applicantName":"Jane Doe","email":"jane@example.com","propertyAddress":"12 Oak St","propertyValue":450000,"yearBuilt":1998,"constructionType":"masonry"}'

# invalid request -> 400 with field-level errors
curl -s -X POST http://localhost:3000/api/quotes \
  -H 'Content-Type: application/json' \
  -d '{"applicantName":"","email":"not-an-email","propertyValue":"lots","yearBuilt":3000,"constructionType":"wood"}'
```

Security lint:

```bash
npm run lint:security   # eslint + eslint-plugin-security
npm run audit           # npm audit
```

## The intentional vulnerability (first draft)

The first draft (commit "Add vulnerable first draft of home insurance quote
API") trusted `req.body` completely — no type checking, no length limits, no
sanitization:

- `propertyValue` and `yearBuilt` were used directly in arithmetic. A missing or
  non-numeric `propertyValue` yields a `NaN` premium; unbounded values produce
  nonsense quotes.
- `applicantName` and `propertyAddress` were echoed back in the response and
  concatenated into a log string with no length limit or sanitization.
- `constructionType` (attacker-controlled) was used directly as a bracket key to
  index a plain object: `RATE_TABLE[constructionType]`. This is a classic
  **object-injection** sink — keys like `__proto__`, `constructor`, or
  `hasOwnProperty` reach unintended object internals instead of the intended data.

### Security lint output — before the fix

`npm run lint:security` flagged the object-injection sink:

```
/…/src/server.js
  35:16  warning  Variable Assigned to Object Injection Sink  security/detect-object-injection

✖ 1 problem (0 errors, 1 warning)
```

## What was fixed and why

1. **Schema validation with `zod`.** All input is validated by a strict schema
   (`quoteRequestSchema.safeParse(req.body)`) before any value is used:
   required fields, correct types, string length bounds, RFC-style email format,
   and numeric ranges for `propertyValue` (positive, finite, capped) and
   `yearBuilt` (integer, 1800–current year). Invalid requests are rejected with
   **HTTP 400** and a clear list of field-level errors. `.strict()` also rejects
   unexpected extra fields. This eliminates `NaN`/nonsense premiums and enforces
   trusted, typed values downstream.

2. **No unsafe dynamic property access.** The rate table is now a `Map` and the
   lookup uses `RATE_TABLE.get(constructionType)`, which is not an
   object-injection sink. `constructionType` is additionally constrained to an
   enum, so only known-good keys are ever used. This resolves the
   `security/detect-object-injection` warning.

3. **No unsanitized echo / string concatenation.** The response now returns only
   validated, length-bounded values, and the unsanitized concatenated log line
   was removed.

### Security lint output — after the fix

```
> eslint src

(no problems — clean)
```

**Best practice:** never trust request input. Validate and coerce it at the
boundary with a schema, reject invalid data with a 4xx, prefer `Map`/allow-lists
over dynamic object bracket access with external keys, and only use typed,
validated values in business logic.
