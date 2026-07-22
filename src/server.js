import express from 'express';

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;

// Base annual premium rates by construction type (per $1000 of property value).
const RATE_TABLE = {
  frame: 4.5,
  masonry: 3.2,
  'fire-resistive': 2.1,
};

// POST /api/quotes
//
// Accepts a home insurance quote request and returns an estimated annual premium.
//
// FIRST DRAFT: this handler trusts req.body completely. There is no type
// checking, no length limiting, and no sanitization. The applicant name is
// echoed straight back into the response, propertyValue is used in arithmetic
// without validating it is a number, and the construction-type rate is looked
// up via non-literal (attacker-controlled) property access.
app.post('/api/quotes', (req, res) => {
  const {
    applicantName,
    email,
    propertyAddress,
    propertyValue,
    yearBuilt,
    constructionType,
  } = req.body;

  // Attacker-controlled key used directly to index an object.
  const rate = RATE_TABLE[constructionType];

  // Age factor derived from unvalidated yearBuilt.
  const age = new Date().getFullYear() - yearBuilt;
  const ageFactor = 1 + age / 100;

  // propertyValue used directly in arithmetic with no numeric validation.
  const annualPremium = (propertyValue / 1000) * rate * ageFactor;

  // applicantName echoed back unsanitized and concatenated into a log string.
  const summary = 'Quote generated for ' + applicantName + ' at ' + propertyAddress;
  console.log(summary);

  res.json({
    applicant: applicantName,
    email,
    propertyAddress,
    constructionType,
    annualPremium,
    summary,
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`Home insurance quote API listening on port ${PORT}`);
});

export default app;
