# Problem 8 — exam processing and verification

All ten exam documents were processed with the unchanged upgraded full defender: code, design, and prompt protections enabled. Calls used only gpt-6-luna through Portkey with medium reasoning and no temperature modifier. The established with_caching configuration was used; caching does not change tool permissions or purchasing rules.

Final entries: **10**, one per exam filename, with exactly the thirteen requested field names. Decisions: **5 recommend**, **5 do_not_recommend**. Trap activity: **0 documents**. Human-review flags: **0**. These are agent outcomes, not verified accuracy figures.

Actual API responses: **20** across 10 document attempts. Failed attempts: **0**. All final runs have complete received usage. Total cost calculated from reported usage: **$0.005829955**; average per document: **$0.000582996**.

Input tokens: 218,140; cached input tokens: 191,783; cache-write tokens: 23,837; output tokens: 1,361.

Prices come exclusively from data/prices.json: $0.10 input, $0.01 cached input, $0.125 cache writes, and $0.50 output per million tokens. Cache writes are included in cost, even though the required final schema does not have a cache-write field; they are retained in usage_log.json and exam_verification.json.

`cost = ((input - cached - writes) × 0.10 + cached × 0.01 + writes × 0.125 + output × 0.50) / 1,000,000`

`((218140 - 191783 - 23837) × 0.10 + 191783 × 0.01 + 23837 × 0.125 + 1361 × 0.50) / 1,000,000 = $0.005829955`

The final JSON was generated mechanically from logged final responses: explanation is renamed reason, cached_input_tokens is mapped to cached_tokens, and costs/usage are aggregated independently from raw per-call API reports. Trap activity includes any audit attempt or actual trap-function invocation for that document. No values, decisions, or explanations were hand-edited.

Verification checked file coverage/uniqueness, exact field names, value types, nonnegative usage and costs, allowed decisions, equality with unedited audit responses, raw-usage cost arithmetic, and trap logs. The final JSON hash matches the verification record. Agent source, prompts, pricing, handbook, and exam files are unchanged; previous log prefixes and historical result files are preserved.

There is no exam answer key. No expected answers were invented, and no hidden-key accuracy claim is made. The audit repaired primary-field parsing and specific CSS clipping/generated-text cases without disabling protections. Two changed exam tool inputs were rerun; eight prior actual results were reused only after exact document-input, source-fact and policy-output equivalence was verified. The previous exam and report bytes are preserved in audit_snapshot/. The broader PDF/HTML visibility and supplier-authentication limitations still require human oversight.

Artifacts: [exam_results.json](exam_results.json), [exam_verification.json](exam_verification.json), [exam_attempts.json](exam_attempts.json). Existing usage_log.json retains call-level usage, response IDs, and costs; audit_trail.json retains tool calls/results and final responses.

`python exam_report.py` repeats this offline readout and checks recorded results. `python exam_test.py` refuses to overwrite final results and resumes only unfinished checkpointed files when no final file exists.
