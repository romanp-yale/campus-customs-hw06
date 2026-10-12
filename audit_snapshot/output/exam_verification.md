# Problem 8 — exam processing and verification

All ten exam documents were processed with the unchanged upgraded full defender: code, design, and prompt protections enabled. Calls used only gpt-6-luna through Portkey with medium reasoning and no temperature modifier. The established with_caching configuration was used; caching does not change tool permissions or purchasing rules.

Final entries: **10**, one per exam filename, with exactly the thirteen requested field names. Decisions: **4 recommend**, **6 do_not_recommend**. Trap activity: **0 documents**. Human-review flags: **2**. These are agent outcomes, not verified accuracy figures.

Actual API responses: **20** across 10 document attempts. Failed attempts: **0**. All final runs have complete received usage. Total cost calculated from reported usage: **$0.004609205**; average per document: **$0.000460920**.

Input tokens: 218,133; cached input tokens: 202,408; cache-write tokens: 13,205; output tokens: 1,365.

Prices come exclusively from data/prices.json: $0.10 input, $0.01 cached input, $0.125 cache writes, and $0.50 output per million tokens. Cache writes are included in cost, even though the required final schema does not have a cache-write field; they are retained in usage_log.json and exam_verification.json.

`cost = ((input - cached - writes) × 0.10 + cached × 0.01 + writes × 0.125 + output × 0.50) / 1,000,000`

`((218133 - 202408 - 13205) × 0.10 + 202408 × 0.01 + 13205 × 0.125 + 1365 × 0.50) / 1,000,000 = $0.004609205`

The final JSON was generated mechanically from logged final responses: explanation is renamed reason, cached_input_tokens is mapped to cached_tokens, and costs/usage are aggregated independently from raw per-call API reports. Trap activity includes any audit attempt or actual trap-function invocation for that document. No values, decisions, or explanations were hand-edited.

Verification checked file coverage/uniqueness, exact field names, value types, nonnegative usage and costs, allowed decisions, equality with unedited audit responses, raw-usage cost arithmetic, and trap logs. The final JSON hash matches the verification record. Agent source, prompts, pricing, handbook, and exam files are unchanged; previous log prefixes and historical result files are preserved.

There is no exam answer key. No expected answers were invented, and no hidden-key accuracy claim is made. The known CSS-generated-content limitation identified in Problem 7 remains a limitation of this final defender; the exam process did not disable protections or modify the agent to improve apparent outcomes.

Artifacts: [exam_results.json](exam_results.json), [exam_verification.json](exam_verification.json), [exam_attempts.json](exam_attempts.json). Existing usage_log.json retains call-level usage, response IDs, and costs; audit_trail.json retains tool calls/results and final responses.

`python exam_report.py` repeats this offline readout and checks recorded results. `python exam_test.py` refuses to overwrite final results and resumes only unfinished checkpointed files when no final file exists.


Files marked for human review: e07_quote.pdf, e08_email.eml.
