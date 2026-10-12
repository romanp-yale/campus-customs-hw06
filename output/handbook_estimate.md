# Problem 2 — Handbook token and cost estimate

## Token count and methodology

The supplied `data/shop_handbook.md` contains **10,069 tokens** under the
`o200k_base` encoding in **tiktoken 0.14.0**. It contains 29,241 Unicode
characters. The complete file was read as bytes and decoded as UTF-8 without
normalizing newlines, stripping whitespace, or removing Markdown. The count is
`len(tiktoken.get_encoding("o200k_base").encode_ordinary(text))`.

This is an exact, reproducible count for that encoding, but an **estimate for
gpt-6-luna**: the installed tiktoken model and prefix maps have no gpt-6-luna
entry, and the official model page does not establish its tokenizer. We use
o200k_base as a modern OpenAI text-tokenizer proxy rather than claiming a
verified model-specific mapping. No measured error bound is available. This is
more text-specific than a characters-per-token heuristic, but its agreement
with gpt-6-luna must be checked against actual usage in Problem 4.

The count covers handbook text alone. It excludes message roles and boundaries,
system instructions, vendor documents, tools, schemas, and generated output.
Official [OpenAI token-counting documentation](https://developers.openai.com/api/docs/guides/token-counting)
explains that local tokenizers have limitations and request structure contributes
additional tokens. The [gpt-6-luna model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna)
was checked for a tokenizer specification. No API calls were made for this estimate.

## Supplied pricing

All monetary rates below come exclusively from the supplied `data/prices.json`,
under the exact model key `gpt-6-luna`. The JSON source label is
`OpenAI Standard pricing, per 1M tokens (MGT 409 Lecture 11)`.

- `input_per_1m`: **$0.10 per 1,000,000 tokens**.
- `cached_input_per_1m`: **$0.01 per 1,000,000 tokens**.
- `cache_write_per_1m`: **$0.125 per 1,000,000 tokens**.
- `output_per_1m`: **$0.50 per 1,000,000 tokens**.

These are assignment-supplied rates, not independently verified live prices.
Output pricing does not enter this handbook-only input estimate. The primary
cached calculation assumes an existing cache and all 10,069 handbook tokens
billed at the cached-input rate; cache creation is discussed separately below.

## Formulas and arithmetic

Let T = 10,069 handbook tokens, M = 1,000,000 tokens per pricing unit,
and N = number of calls.

Uncached input cost = (T × N / M) × $0.10.

Fully cached input cost = (T × N / M) × $0.01.

### One call

- Uncached: (10,069 × 1 / 1,000,000) × $0.10 = **$0.00100690**
  (0.100690 cents).
- Fully cached: (10,069 × 1 / 1,000,000) × $0.01 = **$0.00010069**
  (0.010069 cents).
- Savings: $0.00100690 − $0.00010069 = **$0.00090621**.

### 1,000 calls

Total handbook input = 10,069 × 1,000 = 10,069,000 tokens.

- Uncached: (10,069,000 / 1,000,000) × $0.10
  = 10.069 × $0.10 = **$1.00690000**.
- Fully cached: (10,069,000 / 1,000,000) × $0.01
  = 10.069 × $0.01 = **$0.10069000**.
- Savings: $1.00690000 − $0.10069000 = **$0.90621000**.

For either call count, the cached cost is 0.01 / 0.10 = 0.10 of the uncached
cost: **90% less**, or one tenth as much, assuming full cache hits.

## Cache assumptions and scope

The fully cached totals describe an idealized cache-hit scenario, not a promise
that repeated requests will be cached. A cold start, partial cache hits, cache
expiration, or different request content can change the costs.

The JSON also supplies a cache-write rate. If a particular route bills one full
handbook cache write at that rate, its estimated write cost is
(10,069 / 1,000,000) × $0.125 = **$0.001258625**.
Under a conditional scenario of one such write followed by 999 fully cached
calls, the total is $0.001258625 + (999 × $0.00010069)
= **$0.101847935**. This is separate from the requested 1,000 cache-hit
comparison. The JSON does not specify billing mechanics, so we do not assume
whether write charges replace or supplement normal input charges on the route.

All results are calculated estimates, **not actual API usage measurements**.
They exclude other prompt text, response/reasoning output, and any gateway fees.
Problem 4 will compare the estimates with real usage; it has not been performed.

## Reproduction

From the project root after installing `requirements.txt`, run:

```powershell
python src/estimate_handbook.py
```

The script reads the original handbook and supplied JSON, counts locally, uses
decimal arithmetic, and prints the count, file hash, and both cost scenarios.
For this run, the already-installed Homework 4 environment supplied tiktoken
0.14.0 because package installation in the new environment was unavailable.
The tokenizer vocabulary used for o200k_base was available locally. Neither
the handbook nor the pricing file was modified.
