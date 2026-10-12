# Problem 4 — Measured prompt caching comparison

## Verification and experiment design

Completed **24 main document runs**, 12 per configuration, with **48 actual API responses**.
Cache comparison verified: **True**. All totals below use only this final comparison cohort.

- With caching: `prompt_cache_options={"mode":"implicit","ttl":"30m"}`; unchanged handbook, instructions, tools, schema, model, and reasoning effort form the shared prefix.
- Without caching: `prompt_cache_options={"mode":"explicit","ttl":"30m"}`, no breakpoints, plus a unique initial system-message nonce and unique `prompt_cache_key` on **every model call**, including the call after tool reading.
- The extra nonce prevents prefix reuse on this route; it is labeled metadata and does not change the handbook or purchasing rules. No tokens or numbers in the handbook were altered.
- Each request forces a Portkey response-cache refresh and uses a unique trace ID. Prompt-cache reuse inside the provider is the subject of this experiment; replaying whole responses would invalidate it.
- Runs were paired by document with alternating configuration order; interrupted experiment recovery retained completed cached runs. Calls were sequential, with no separate prewarming call. Earlier homework runs could already have warmed the stable prefix.

The [OpenAI prompt-caching guide](https://developers.openai.com/api/docs/guides/prompt-caching) documents that explicit-only mode without breakpoints should avoid cache reads and writes. **This Portkey route still returned cached tokens under that setting alone.** The initial control could not be verified; the exact gateway/provider component responsible is not established. Prefix isolation was therefore added and verified using actual counters, rather than assuming the requested setting worked.

## Actual usage and costs

Prices come exclusively from `data/prices.json`: input $0.10, cached input $0.01, cache write $0.125, and output $0.50 per million tokens.

For every response:

```text
uncached_input = input_tokens - cached_tokens - cache_write_tokens
cost = (uncached_input * 0.10 + cached_tokens * 0.01
        + cache_write_tokens * 0.125 + output_tokens * 0.50) / 1,000,000
```

Cache writes and reads are partitions of total input; they are not charged again at the ordinary input rate. Output includes reported reasoning tokens without double counting. Every raw usage object, including other available counters, is preserved in `cache_test.json`. Costs are calculated from actual token usage at the assignment rates, not independently verified provider invoices.

### With caching

- Documents: 12; API calls: 24.
- Input: 257,949; cached input: 253,328; cache writes: 1,597; output: 2,839.
- Cache verification: True; complete successful usage: True.
- Total cost: **$0.004454805**.
- Average per document = $0.004454805 / 12 = **$0.000371234**.
- Cost components: uncached_input $0.0003024; cached_input $0.00253328; cache_writes $0.000199625; output $0.0014195.

### Without caching (zero reuse)

- Documents: 12; API calls: 24.
- Input: 258,838; cached input: 0; cache writes: 255,814; output: 2,963.
- Cache verification: True; complete successful usage: True.
- Total cost: **$0.033760650**.
- Average per document = $0.033760650 / 12 = **$0.002813388**.
- Cost components: uncached_input $0.0003024; cached_input $0.00; cache_writes $0.03197675; output $0.0014815.

### Savings

Savings = ($0.033760650 − $0.004454805) / $0.033760650 × 100 = **86.80%**.

The cached configuration reports real cache reads. Every final no-cache call explicitly reports zero cached tokens. However, the no-cache route still writes cache entries; those writes are charged in the measured comparison. This is **zero reuse**, not a verified route that disables cache writes.

## Comparison with Problem 2

Problem 2 counted 10,069 handbook tokens with tiktoken/o200k_base and estimated handbook-only costs per model call: $0.00100690 uncached or $0.00010069 fully cached, a 90% input-only reduction. For 1,000 calls: $1.00690 versus $0.10069.

Each document here required two model calls, each containing the handbook. A handbook-only two-call/document projection would be $0.00201380 uncached or $0.00020138 cached. For 12 documents (24 calls per configuration), the corresponding theoretical handbook-only totals are $0.02416560 and $0.00241656.

The actual agent costs are $0.033760650 and $0.004454805, respectively. They also include tools, schema, prompt/message formatting, document content, model output, and cache writes. The no-cache isolation prefix adds a small token overhead. These totals therefore do not directly test the handbook-only tokenizer count: the API does not itemize handbook tokens separately.

## Projection: 1,000 documents/day for 30 days

Volume = 1,000 × 30 = **30,000 documents**. Scale each measured average by 30,000:

- With caching: ($0.004454805 / 12) × 30,000 = **$11.137012**.
- Without cache reuse: ($0.033760650 / 12) × 30,000 = **$84.401625**.
- Projected savings: **$73.264612**.

These are extrapolations, not observed 30-day bills. They assume the same document mix, two-call workflow, cache-hit pattern, cache-write behavior, and prices. Cold starts, retention expiration, changed prompts, concurrency, retries, different output lengths, and gateway fees can change actual costs. Warm-cache daily averages may understate cold-start costs.

## Surprising results and limits

- The explicit-only parameter was serialized correctly, yet initial no-cache attempts reported nonzero cached tokens. Four unsuccessful control runs (eight calls) are preserved separately, not included as successful no-cache data.
- Those preliminary control calls cost $0.001526635 using the supplied rates. One additional interrupted setup attempt has no saved usage and unknown cost; it is not assigned zero. The requested 24-run final cohort therefore required extra setup attempts.
- Prefix isolation eliminated reads but did not eliminate cache writes. This adds the supplied 25% cache-write premium over ordinary input pricing and raises the measured zero-reuse baseline. Savings should not be presented as a clean “all ordinary input versus all cached input” experiment.
- The cached configuration reuses more than the handbook alone, including stable tools and instructions. It nevertheless still sends the full handbook on every request; caching changes token billing, not the local request contents.
- Both configurations use the same baseline agent. Several practice answers differ from the supplied key; the mismatches are recorded in the JSON summary. Cached and noncached purchasing facts agree for each document in this cohort, but caching does not establish factual correctness or prompt-injection safety. Those concerns remain for later problems.
- A bookkeeping pass mistakenly marked an in-progress p08 run as interrupted. Its later successful usage record and a correction event supersede that interim marker; no successful usage was dropped or counted twice.

## Artifacts and reproduction

- `output/cache_test.json`: final run records, per-call actual usage/output/cost, request cache settings, explicit verification flags, preliminary failed controls, interrupted attempt, and calculated summary.
- `output/usage_log.json` and `output/audit_trail.json`: existing records preserved with new runs appended; simulated trap attempts remain in `output/trap_calls.json`.
- `python cache_test.py`: starts the live experiment or resumes its saved cohort; it does not overwrite completed pairs.
- `python cache_report.py`: validates and reproduces this report from the saved API evidence without any new model calls.

Caching meaningfully reduces this measured agent’s token cost, subject to the verified route-specific cache-write caveat and the small, warm-cache sample. No future security defenses were introduced.
