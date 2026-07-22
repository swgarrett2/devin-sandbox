import express from 'express';
import { z } from 'zod';

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;

// Base annual premium rates by construction type (per $1000 of property value).
// A Map is used instead of a plain object so the lookup key cannot reach an
// object-injection sink (e.g. "__proto__"/"constructor") via bracket access.
const RATE_TABLE = new Map([
  ['frame', 4.5],
  ['masonry', 3.2],
  ['fire-resistive', 2.1],
]);

const CONSTRUCTION_TYPES = ['frame', 'masonry', 'fire-resistive'];

const CURRENT_YEAR = new Date().getFullYear();

// Server-side schema. Every field is required, typed, length-bounded, and
// range-checked. Unknown fields are stripped and the request is rejected if any
// constraint fails.
const quoteRequestSchema = z
  .object({
    applicantName: z.string().trim().min(1).max(100),
    email: z.string().trim().email().max(254),
    propertyAddress: z.string().trim().min(1).max(200),
    propertyValue: z.number().finite().positive().max(1_000_000_000),
    yearBuilt: z.number().int().min(1800).max(CURRENT_YEAR),
    constructionType: z.enum(CONSTRUCTION_TYPES),
  })
  .strict();

// POST /api/quotes
//
// Accepts a home insurance quote request and returns an estimated annual
// premium. All input is validated and coerced through quoteRequestSchema before
// any value is used, so downstream arithmetic and lookups only ever see typed,
// bounded data.
app.post('/api/quotes', (req, res) => {
  const parsed = quoteRequestSchema.safeParse(req.body);

  if (!parsed.success) {
    return res.status(400).json({
      error: 'Invalid quote request',
      details: parsed.error.issues.map((issue) => ({
        field: issue.path.join('.'),
        message: issue.message,
      })),
    });
  }

  const {
    applicantName,
    email,
    propertyAddress,
    propertyValue,
    yearBuilt,
    constructionType,
  } = parsed.data;

  // constructionType is constrained to the enum, and Map#get is not an
  // object-injection sink.
  const rate = RATE_TABLE.get(constructionType);

  const age = CURRENT_YEAR - yearBuilt;
  const ageFactor = 1 + age / 100;

  const annualPremium =
    Math.round((propertyValue / 1000) * rate * ageFactor * 100) / 100;

  return res.status(200).json({
    applicant: applicantName,
    email,
    propertyAddress,
    constructionType,
    annualPremium,
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`Home insurance quote API listening on port ${PORT}`);
});

export default app;
