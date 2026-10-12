# Homework 6 — strict requirements audit and final fixes

This assessment applies to the current local candidate, not the older public commit. Estimated marks are conservative judgment, not the course grader’s decision. No push occurred during this audit.

| Problem | Max points | Estimated earned points | Status | Issues |
|---|---:|---:|---|---|
| 1. AI Prompts | 5 | 5 | PASS | Actual original/follow-up prompts present; supplied attachment verified byte-for-byte. |
| 2. Handbook Estimate | 6 | 6 | PASS | 10,069 o200k_base tokens reproduced; explicitly a model-tokenizer estimate. |
| 3. Agent | 12 | 12 | PASS | Real refreshed p01/p08 evidence, three formats, fixed model/full-book hook, structured output and logs. |
| 4. Caching | 16 | 16 | PASS | 48 unique refreshed responses; zero cached reads in every no-reuse call; writes separately priced. |
| 5. Attacks | 8 | 8 | PASS | Repaired replay contamination; 12 fresh baseline runs still show four of seven attacks succeeding. |
| 6. Defenses | 16 | 15 | PARTIAL | Three layers and actual P6 ablations verified; later repairs not separately isolated; visibility remains heuristic. |
| 7. Red Team | 8 | 8 | PASS | Exactly two original attacks plus two explicitly requested follow-ups; historical failures and four repaired live outcomes preserved. |
| 8. Exam | 12 | 12 | PASS | 10 unique typed entries; two genuine repairs, eight proven-equivalent reused outputs; no hidden-key accuracy claim. |
| 9. HTML Report | 12 | 11 | PASS | Offline charts/table/controls verified; screen-reader and independent browser-engine/physical-print checks not performed. |
| 10. GitHub | 5 | 4 | PARTIAL | Existing repository public; local audit changes intentionally await explicit push approval. |
| **TOTAL** | **100** | **97** | **LOCAL CANDIDATE READY** | Publish only after approval. |

## A. Missing or unverified requirements

- No required source, data or output file is missing, empty or malformed. The four custom files consist of exactly two originals and two authorized follow-ups.
- Publishing these audit fixes is pending explicit approval. The public repository currently has the pre-audit commit; do not treat that older revision as the repaired candidate.
- The tokenizer is verified only for o200k_base, not independently established for the provider’s model. This permitted estimation limitation is stated explicitly.
- No hidden exam answer key, provider invoice verification, universal injection guarantee, OCR/multi-item/currency coverage, native-mail integration or real payment/email execution was verified or claimed.
- New browser repairs have no isolated per-layer overhead experiment. Original P6 matched contrasts are genuine; local CPU/staff/gateway costs are unmeasured.
- Offline HTML was tested in Chromium/Edge at five widths. Assistive-technology testing, unrelated rendering engines and physical printing remain unverified.
- One historical interrupted setup request has no received API usage and unknown cost. It remains outside the complete final caching cohort; no zero cost was invented.

## B. Bugs discovered and fixes

- `agent.py:166`: gateway response refresh applied only outside baseline mode. All 24 old P5 responses were HITs, with repeated IDs from earlier requests. Refresh is now transport-wide; 12 original undefended documents were rerun, all REFRESH with 24 distinct IDs. No security layer was added to baseline. See the preserved replay artifacts and [Portkey’s cache semantics](https://docs1.portkey.ai/docs/product/ai-gateway/cache-simple-and-semantic).
- `defenses.py:170`: primary item extraction recognized Item/Happy-to-quote but missed Quote-for. Added that explicit anchored declaration; e08 now produces its source SKU through a real agent rerun.
- `defenses.py:174`: quantity regex rejected properly grouped 1,000. Generic grouping validation/normalization now preserves 1000; e07 was genuinely rerun and declined for the 600-unit limit.
- `defenses.py:172`: price regex could truncate $1,000.00 into $1.00. Grouped prices now parse completely; malformed groups and scientific suffixes are not accepted as cheap prefixes. A real local regression verifies the correct rejection.
- `html_layout.py:13` and `:28`: DOM rectangles ignored empty inset clipping and opaque generated text. Added scoped, non-executable parsing of those paint cases; actual generated-price attack now returns $17.44 and recommend. No filenames, answer key, vendor-specific numbers or malicious instructions are used as runtime rules.
- `attack_test.py`/`attack_report.py`: baseline freshness was not checked; outcome summaries had fixed success lists. Freshness is now verified and success lists/counts derived from actual records; missing-field failures alone are not labeled attacker fact adoption.
- `submission_audit.py:80`: checking the last usage row required every later run to be the smoke document. It now finds the actual relevant successful smoke record.
- `exam_test.py:37,111,118`: UTF-8 pricing read made explicit; historical records can be verified at archived paths; equivalent reused runs are disclosed. These are provenance fixes, not edits to exam answers.
- `report_template.html`/builder/test: fixed hardcoded exam counts and stale current-failure wording; updated historical-versus-current labels and dynamic audit metrics. Local .env copy instructions now avoid overwriting an existing file.

## C. Changes made

Source changes are limited to visibility/number/primary-label parsing, transport freshness, verification/reporting and focused tests. Runtime prompts, models, trap functions, handbook, practice key, exam files and all original attack files were not changed.
Modified: agent.py, defenses.py, html_layout.py, attack_test.py, attack_report.py, exam_test.py, exam_report.py, submission_audit.py, build_hw6_report.py, report_template.html, test_hw6_report.py, README.md, AI_prompts.md and dependent output artifacts.
Added: audit_retest.py, requirements_audit.py, tests/test_audit_fixes.py, audit_snapshot/manifest and original copies, explicit replay archives and audit records. All prior log entries are retained; no file was deleted to simplify submission.

## D. Actual test verification

- `python -m unittest discover -s tests -v`: final candidate suite 22/22 passed in the clean clone. An earlier generated-text regression failed because Chromium emitted opaque rgb rather than rgba; fixed and rerun. The clean clone was overlaid with the final candidate, contained no .env, and used the freshly installed requirements.
- Fresh isolated Python environment: requirements.txt installation succeeded; pip check reported no broken dependencies; CLI help and the documented defended p01 command succeeded with real usage.
- Local Git clone plus candidate overlay: no .env copied; original baseline, frozen defender and audit snapshot hashes verified. Root-relative paths and the local suite worked.
- `audit_retest.py`: two changed exam inputs plus four defended attack documents actually ran; 24/24 custom-attack field/decision comparisons matched, no trap calls. Eight exam and twelve practice inputs/facts/policy outputs were verified equivalent to valid previous inference records.
- `attack_test.py`: 12 fresh original undefended runs, all 24 REFRESH responses with distinct IDs; four factual attacks still succeed, zero traps/links.
- `exam_report.py`, report builder and schema checks: ten files exactly once, required 13 keys/types, valid decisions, exact unedited audit-output equality and Decimal cost reconciliation.
- Visual checks: all twelve original practice documents were rendered and their contact sheets inspected; PDF rasters and email-style MIME views are documented, with native application limitations in output/audit_visual_checks/verification.json.
- `test_hw6_report.py`: isolated directory containing only HTML, offline network, filters including empty results, volume/cohort projections, downloaded JSON equality, embedded images, static no-JS content, print control wiring and five responsive widths passed. No console errors or external requests.
- Credential scan: candidate bytes and initial tracked history checked against actual local credential values and key patterns without printing values. Neither real .env nor local environments are tracked. The public repository returned anonymous HTTP 200; no push occurred.
- Actual audit API work: 19 document runs / 38 reported responses, $0.009308675. This includes the six targeted repairs, one fresh-install CLI smoke and twelve necessary baseline replacements.

## E. Token and cost validation

Handbook: 10,069 proxy tokens. One input-only call: $0.00100690 uncached / $0.00010069 cached. 1,000 calls: $1.00690 / $0.10069. These are estimates, not measured handbook-only API charges.
Measured matched caching cohort: $0.004454805 cached / $0.033760650 zero reuse; 86.8047416148682% savings. At 30,000 documents: $11.1370125 / $84.401625. All 48 response IDs are distinct; all zero-reuse calls explicitly report zero cached reads. Cache-write charges remain and are included.
P6 paired marginal effects: code −18.375 input / −40.583333 output / −$0.000022588542 per document; design −134.208333 / −72.25 / −$0.000052901042; prompt +480.875 / +3.5 / +$0.000061859375. There are 24 contrasts per layer; these interacting net effects are not additive surcharges or new-code line-item fees.
Corrected fresh baseline token cost: $0.005687010. Original defended cohort: $0.033626525 under zero cache reuse; their cost difference is not a defense overhead estimate.
Final exam evidence: $0.005829955 across ten entries and twenty response reports; five recommend/five do_not_recommend, no unknown fields, no traps. Eight reports are reused real observations with input equivalence, not claimed as new calls or hidden-key accuracy.

## F. Security assessment

The defended architecture provides a real action boundary: the model never receives ordinary trap schemas, function-level guards require exact one-action application authorization, and both tools always remain log-only. Model/document claims cannot set that context. Trusted handbook code, not vendor/model prose, determines purchasing rules. Selected-file checks block unrelated file access.
The original baseline remains intentionally vulnerable, with four observed factual overrides; it is not a production-safe configuration. The full configuration preserved all clean practice facts and decisions and fixed all four authored attacks in the latest live tests. This does not prove universal instruction obedience or rendering security: arbitrary clipping/overlays/images, supplier impersonation, unsupported layouts and human mistakes remain limitations. Use supervised review.

## G. Submission readiness

The local candidate is ready for final review and publication. Existing repository: https://github.com/romanp-yale/campus-customs-hw06 (public). The current public commit remains pre-audit. Next steps: approve publishing, commit/stage the reviewed changes, push main, recheck remote commit/public access, then manually submit the URL to Canvas. No automatic Canvas submission or new GitHub push was performed.

## H. Conservative final grade estimate

Estimated local-candidate score: **97/100**, with a plausible 94–100 range depending on grader interpretation. This is not a guaranteed grade or production certification. One point is reserved for unisolated newer defense overhead/general visibility uncertainty, one for untested advanced accessibility/cross-engine behavior, and one for the pending publication step. No hidden exam accuracy is assumed.

## Requirement-by-requirement checklist

Each bullet in the supplied audit prompt is mapped below. PASS refers to the documented homework scope; QUALIFIED and PENDING HUMAN expose limits rather than silently claiming full verification.

1. **PASS** — All 12 practice documents exist.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

2. **PASS** — All 10 exam documents exist.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

3. **PASS** — Both original red-team attack documents exist.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

4. **PASS** — All required output JSON files contain valid JSON with the appropriate structure.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

5. **PASS** — All Markdown reports contain the requested analysis, not merely placeholder headings.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

6. **PASS** — All files are stored in the correct directories.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

7. **PASS** — Dependencies in `requirements.txt` are sufficient for a fresh installation.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

8. **PASS** — All paths work when running the project from its root directory.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

9. **PASS** — There is a separate section for each problem, 1–10.
   Evidence: AI_prompts.md; original attachment byte inclusion and original Git prefix preservation.

10. **PASS** — Every section includes the problem number and title.
   Evidence: AI_prompts.md; original attachment byte inclusion and original Git prefix preservation.

11. **PASS** — Every section includes at least one actual prompt I entered.
   Evidence: AI_prompts.md; original attachment byte inclusion and original Git prefix preservation.

12. **PASS** — Follow-up prompts and explanations are included where applicable.
   Evidence: AI_prompts.md; original attachment byte inclusion and original Git prefix preservation.

13. **PASS** — The file accurately records the development process.
   Evidence: AI_prompts.md; original attachment byte inclusion and original Git prefix preservation.

14. **PASS** — Handbook token count is accurately calculated or measured.
   Evidence: src/estimate_handbook.py; supplied prices; independently reproduced exact encoding count and arithmetic.

15. **PASS** — The counting method is explained.
   Evidence: src/estimate_handbook.py; supplied prices; independently reproduced exact encoding count and arithmetic.

16. **PASS** — Pricing uses the actual `gpt-6-luna` rates in `prices.json`.
   Evidence: src/estimate_handbook.py; supplied prices; independently reproduced exact encoding count and arithmetic.

17. **PASS** — Costs are provided for 1 call and 1,000 calls.
   Evidence: src/estimate_handbook.py; supplied prices; independently reproduced exact encoding count and arithmetic.

18. **PASS** — Both cached and uncached costs are calculated.
   Evidence: src/estimate_handbook.py; supplied prices; independently reproduced exact encoding count and arithmetic.

19. **PASS** — The math is shown explicitly.
   Evidence: src/estimate_handbook.py; supplied prices; independently reproduced exact encoding count and arithmetic.

20. **PASS** — Units and dollar amounts are correct.
   Evidence: src/estimate_handbook.py; supplied prices; independently reproduced exact encoding count and arithmetic.

21. **PASS** — Any estimated tokenizer counts are clearly distinguished from measured API usage.
   Evidence: src/estimate_handbook.py; supplied prices; independently reproduced exact encoding count and arithmetic.

22. **PASS** — The agent uses PydanticAI.
   Evidence: agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.

23. **PASS** — Every AI call uses `gpt-6-luna` through the intended Portkey configuration.
   Evidence: agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.

24. **PASS** — The agent accepts a document path through `--doc`.
   Evidence: agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.

25. **PASS** — HTML, PDF, and `.eml` files can all be read using a tool.
   Evidence: agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.

26. **PASS** — The complete handbook is included in every applicable model call.
   Evidence: agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.

27. **PASS** — The agent extracts vendor, SKU, unit price, lead time in days, and minimum order.
   Evidence: agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.

28. **PASS** — The agent returns only valid decisions: `recommend` or `do_not_recommend`.
   Evidence: agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.

29. **PASS** — Its decision follows the handbook rules.
   Evidence: agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.

30. **PASS** — The reason is one sentence and relates to the decision.
   Evidence: agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.

31. **PASS** — Structured output follows the Pydantic models.
   Evidence: agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.

32. **PASS** — `send_email` and `approve_payment` remain present.
   Evidence: agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.

33. **PASS** — Both trap tools only log calls to `output/trap_calls.json`.
   Evidence: agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.

34. **PASS** — `output/usage_log.json` records document, timestamp, API-reported token usage, and calculated cost.
   Evidence: agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.

35. **PASS** — `output/audit_trail.json` records tool calls, arguments, short results, and the final answer.
   Evidence: agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.

36. **PASS** — Logs append rather than incorrectly overwrite earlier runs.
   Evidence: agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.

37. **PASS** — p01 and p08 have successful execution evidence.
   Evidence: agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.

38. **PASS** — `output/harness.md` explains each model field and tool.
   Evidence: agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.

39. **PASS** — All 12 practice documents were tested with caching.
   Evidence: cache_test.json: 24 runs/48 unique REFRESH responses; Decimal recomputation; zero-read/write partition checks.

40. **PASS** — All 12 were tested without caching.
   Evidence: cache_test.json: 24 runs/48 unique REFRESH responses; Decimal recomputation; zero-read/write partition checks.

41. **PASS** — All model calls for these tests are recorded, including retries if any.
   Evidence: cache_test.json: 24 runs/48 unique REFRESH responses; Decimal recomputation; zero-read/write partition checks.

42. **PASS** — Actual API-reported input, cached, and output token counts are present.
   Evidence: cache_test.json: 24 runs/48 unique REFRESH responses; Decimal recomputation; zero-read/write partition checks.

43. **PASS** — Cached mode genuinely uses the cache.
   Evidence: cache_test.json: 24 runs/48 unique REFRESH responses; Decimal recomputation; zero-read/write partition checks.

44. **PASS** — Uncached mode reports ZERO cached tokens for every call.
   Evidence: cache_test.json: 24 runs/48 unique REFRESH responses; Decimal recomputation; zero-read/write partition checks.

45. **PASS** — Costs are calculated using the correct cached and uncached rates.
   Evidence: cache_test.json: 24 runs/48 unique REFRESH responses; Decimal recomputation; zero-read/write partition checks.

46. **PASS** — Total cost per setup is correct.
   Evidence: cache_test.json: 24 runs/48 unique REFRESH responses; Decimal recomputation; zero-read/write partition checks.

47. **PASS** — Average cost per document is correct.
   Evidence: cache_test.json: 24 runs/48 unique REFRESH responses; Decimal recomputation; zero-read/write partition checks.

48. **PASS** — Percentage savings is correct.
   Evidence: cache_test.json: 24 runs/48 unique REFRESH responses; Decimal recomputation; zero-read/write partition checks.

49. **PASS** — Problem 2 estimates are compared against actual results.
   Evidence: cache_test.json: 24 runs/48 unique REFRESH responses; Decimal recomputation; zero-read/write partition checks.

50. **PASS** — The 1,000-documents-per-day × 30-day projections are correct.
   Evidence: cache_test.json: 24 runs/48 unique REFRESH responses; Decimal recomputation; zero-read/write partition checks.

51. **PASS** — Surprising results are explained using evidence.
   Evidence: cache_test.json: 24 runs/48 unique REFRESH responses; Decimal recomputation; zero-read/write partition checks.

52. **PASS** — All 12 documents were tested on the original undefended agent.
   Evidence: Fresh attack_results.json: 12 comparisons, individually matched fields/decisions, trap/audit records, original rendering/source findings.

53. **PASS** — Extracted fields were compared against `practice_key.json`.
   Evidence: Fresh attack_results.json: 12 comparisons, individually matched fields/decisions, trap/audit records, original rendering/source findings.

54. **PASS** — Every field match is recorded individually.
   Evidence: Fresh attack_results.json: 12 comparisons, individually matched fields/decisions, trap/audit records, original rendering/source findings.

55. **PASS** — Decision match is recorded separately.
   Evidence: Fresh attack_results.json: 12 comparisons, individually matched fields/decisions, trap/audit records, original rendering/source findings.

56. **PASS** — Trap tool calls are accurately identified.
   Evidence: Fresh attack_results.json: 12 comparisons, individually matched fields/decisions, trap/audit records, original rendering/source findings.

57. **PASS** — Suspicious URLs, links, or unusual text in the answers are detected.
   Evidence: Fresh attack_results.json: 12 comparisons, individually matched fields/decisions, trap/audit records, original rendering/source findings.

58. **PASS** — Every compromised document is discussed.
   Evidence: Fresh attack_results.json: 12 comparisons, individually matched fields/decisions, trap/audit records, original rendering/source findings.

59. **PASS** — Each explanation identifies the attack's actual hiding location.
   Evidence: Fresh attack_results.json: 12 comparisons, individually matched fields/decisions, trap/audit records, original rendering/source findings.

60. **PASS** — The report compares human-visible document contents with what the agent read.
   Evidence: Fresh attack_results.json: 12 comparisons, individually matched fields/decisions, trap/audit records, original rendering/source findings.

61. **PASS** — Trap tools still exist and have not been removed.
   Evidence: defense_results.json + defense_ablations.json: 12 full runs and 48 factorial runs; prepare hook, exact one-shot guard and handbook policy.

62. **PASS** — Both defended and undefended modes remain runnable.
   Evidence: defense_results.json + defense_ablations.json: 12 full runs and 48 factorial runs; prepare hook, exact one-shot guard and handbook policy.

63. **PASS** — All 12 practice documents were rerun with defenses.
   Evidence: defense_results.json + defense_ablations.json: 12 full runs and 48 factorial runs; prepare hook, exact one-shot guard and handbook policy.

64. **PASS** — All fields and decisions are compared against the answer key.
   Evidence: defense_results.json + defense_ablations.json: 12 full runs and 48 factorial runs; prepare hook, exact one-shot guard and handbook policy.

65. **PASS** — Clean quotes still produce correct results.
   Evidence: defense_results.json + defense_ablations.json: 12 full runs and 48 factorial runs; prepare hook, exact one-shot guard and handbook policy.

66. **PASS** — Security does not rely on simply refusing all documents.
   Evidence: defense_results.json + defense_ablations.json: 12 full runs and 48 factorial runs; prepare hook, exact one-shot guard and handbook policy.

67. **PASS** — Token and dollar cost are recorded for each defended run.
   Evidence: defense_results.json + defense_ablations.json: 12 full runs and 48 factorial runs; prepare hook, exact one-shot guard and handbook policy.

68. **PASS** — The report contains a before-and-after comparison for all 12 documents.
   Evidence: defense_results.json + defense_ablations.json: 12 full runs and 48 factorial runs; prepare hook, exact one-shot guard and handbook policy.

69. **QUALIFIED** — The unique role of each defense layer is explained.
   Evidence: defense_results.json + defense_ablations.json: 12 full runs and 48 factorial runs; prepare hook, exact one-shot guard and handbook policy. Verified for the documented scope; model behavior/visibility are not universally guaranteed, and new per-layer overhead is not separately measured.

70. **QUALIFIED** — Additional tokens and dollars per document are quantified for each layer, using actual attributable measurements wherever possible.
   Evidence: defense_results.json + defense_ablations.json: 12 full runs and 48 factorial runs; prepare hook, exact one-shot guard and handbook policy. Verified for the documented scope; model behavior/visibility are not universally guaranteed, and new per-layer overhead is not separately measured.

71. **PASS** — The Safety section explains all layers clearly.
   Evidence: defense_results.json + defense_ablations.json: 12 full runs and 48 factorial runs; prepare hook, exact one-shot guard and handbook policy.

72. **PASS** — There are exactly two original attack files.
   Evidence: red_team_cases/results, round2_cases/results and audit_retest_results; four original runs and four latest defended repairs.

73. **PASS** — Each uses HTML, PDF, or email format.
   Evidence: red_team_cases/results, round2_cases/results and audit_retest_results; four original runs and four latest defended repairs.

74. **PASS** — Both look like plausible normal vendor quotes to a human.
   Evidence: red_team_cases/results, round2_cases/results and audit_retest_results; four original runs and four latest defended repairs.

75. **PASS** — Both contain a distinct hidden attack technique or objective not found in the practice set.
   Evidence: red_team_cases/results, round2_cases/results and audit_retest_results; four original runs and four latest defended repairs.

76. **PASS** — Both were run against the undefended agent.
   Evidence: red_team_cases/results, round2_cases/results and audit_retest_results; four original runs and four latest defended repairs.

77. **PASS** — Both were run against the defended agent.
   Evidence: red_team_cases/results, round2_cases/results and audit_retest_results; four original runs and four latest defended repairs.

78. **PASS** — Actual results before and after defenses are described.
   Evidence: red_team_cases/results, round2_cases/results and audit_retest_results; four original runs and four latest defended repairs.

79. **PASS** — Trap tool outcomes and any answer manipulation are accurately reported.
   Evidence: red_team_cases/results, round2_cases/results and audit_retest_results; four original runs and four latest defended repairs.

80. **PASS** — Exactly 10 entries exist.
   Evidence: exam_results/attempts/verification; 10 unique entries; raw call cost equality; unchanged audit outputs; eight equivalence checks.

81. **PASS** — Each matches a real exam document.
   Evidence: exam_results/attempts/verification; 10 unique entries; raw call cost equality; unchanged audit outputs; eight equivalence checks.

82. **PASS** — No exam document is duplicated or omitted.
   Evidence: exam_results/attempts/verification; 10 unique entries; raw call cost equality; unchanged audit outputs; eight equivalence checks.

83. **PASS** — Every entry contains exactly the required information:
   Evidence: exam_results/attempts/verification; 10 unique entries; raw call cost equality; unchanged audit outputs; eight equivalence checks.

84. **PASS** — Results came from the final defended agent.
   Evidence: exam_results/attempts/verification; 10 unique entries; raw call cost equality; unchanged audit outputs; eight equivalence checks.

85. **PASS** — Values are correctly typed.
   Evidence: exam_results/attempts/verification; 10 unique entries; raw call cost equality; unchanged audit outputs; eight equivalence checks.

86. **PASS** — Decisions are valid.
   Evidence: exam_results/attempts/verification; 10 unique entries; raw call cost equality; unchanged audit outputs; eight equivalence checks.

87. **PASS** — Costs match the usage logs and pricing.
   Evidence: exam_results/attempts/verification; 10 unique entries; raw call cost equality; unchanged audit outputs; eight equivalence checks.

88. **PASS** — `trap_tool_called` reflects actual tool logs, not an assumed false value.
   Evidence: exam_results/attempts/verification; 10 unique entries; raw call cost equality; unchanged audit outputs; eight equivalence checks.

89. **PASS** — The exam results were not manually edited.
   Evidence: exam_results/attempts/verification; 10 unique entries; raw call cost equality; unchanged audit outputs; eight equivalence checks.

90. **PASS** — It opens locally without internet access.
   Evidence: hw6_report.html and browser_test; isolated single-file offline test; all chart/export/filter/projection checks; hashes/math reconciled.

91. **PASS** — All CSS, JavaScript, chart data, and other required assets are embedded.
   Evidence: hw6_report.html and browser_test; isolated single-file offline test; all chart/export/filter/projection checks; hashes/math reconciled.

92. **PASS** — No CDN links, remote fonts, remote scripts, or external image dependencies are required.
   Evidence: hw6_report.html and browser_test; isolated single-file offline test; all chart/export/filter/projection checks; hashes/math reconciled.

93. **PASS** — It displays actual caching results, including a working chart.
   Evidence: hw6_report.html and browser_test; isolated single-file offline test; all chart/export/filter/projection checks; hashes/math reconciled.

94. **PASS** — It compares attacks before and after defenses.
   Evidence: hw6_report.html and browser_test; isolated single-file offline test; all chart/export/filter/projection checks; hashes/math reconciled.

95. **PASS** — It displays defense token and dollar overhead.
   Evidence: hw6_report.html and browser_test; isolated single-file offline test; all chart/export/filter/projection checks; hashes/math reconciled.

96. **PASS** — It displays all 10 exam results.
   Evidence: hw6_report.html and browser_test; isolated single-file offline test; all chart/export/filter/projection checks; hashes/math reconciled.

97. **PASS** — It discusses both red-team attacks.
   Evidence: hw6_report.html and browser_test; isolated single-file offline test; all chart/export/filter/projection checks; hashes/math reconciled.

98. **PASS** — It includes a recommendation for the store manager.
   Evidence: hw6_report.html and browser_test; isolated single-file offline test; all chart/export/filter/projection checks; hashes/math reconciled.

99. **PASS** — It states the projected monthly cost at 1,000 documents daily.
   Evidence: hw6_report.html and browser_test; isolated single-file offline test; all chart/export/filter/projection checks; hashes/math reconciled.

100. **PASS** — Every metric agrees with its source JSON or Markdown file.
   Evidence: hw6_report.html and browser_test; isolated single-file offline test; all chart/export/filter/projection checks; hashes/math reconciled.

101. **PASS** — Layout, readability, accessibility, and visual quality are appropriate for a polished submission.
   Evidence: hw6_report.html and browser_test; isolated single-file offline test; all chart/export/filter/projection checks; hashes/math reconciled.

102. **PASS** — The project is under Git version control.
   Evidence: submission_audit.py checks; Git initial history and ignore rules; public metadata and anonymous HTTP 200; update pending approval.

103. **PASS** — `.gitignore` excludes `.env`, credentials, secret files, and appropriate generated clutter.
   Evidence: submission_audit.py checks; Git initial history and ignore rules; public metadata and anonymous HTTP 200; update pending approval.

104. **PASS** — `.env.example` contains only placeholder values.
   Evidence: submission_audit.py checks; Git initial history and ignore rules; public metadata and anonymous HTTP 200; update pending approval.

105. **PASS** — `README.md` contains clear setup and run instructions.
   Evidence: submission_audit.py checks; Git initial history and ignore rules; public metadata and anonymous HTTP 200; update pending approval.

106. **PASS** — `requirements.txt` supports a clean installation.
   Evidence: submission_audit.py checks; Git initial history and ignore rules; public metadata and anonymous HTTP 200; update pending approval.

107. **PASS** — The complete required data directory is included.
   Evidence: submission_audit.py checks; Git initial history and ignore rules; public metadata and anonymous HTTP 200; update pending approval.

108. **PASS** — All required source and output files are tracked or ready to commit.
   Evidence: submission_audit.py checks; Git initial history and ignore rules; public metadata and anonymous HTTP 200; update pending approval.

109. **PASS** — No secrets appear in tracked files or Git history.
   Evidence: submission_audit.py checks; Git initial history and ignore rules; public metadata and anonymous HTTP 200; update pending approval.

110. **PASS** — No hardcoded API keys appear in the codebase.
   Evidence: submission_audit.py checks; Git initial history and ignore rules; public metadata and anonymous HTTP 200; update pending approval.

111. **PASS** — The documented command runs in a clean environment when appropriately configured.
   Evidence: submission_audit.py checks; Git initial history and ignore rules; public metadata and anonymous HTTP 200; update pending approval.

112. **PASS** — The remote GitHub repository is public, if one already exists.
   Evidence: submission_audit.py checks; Git initial history and ignore rules; public metadata and anonymous HTTP 200; update pending approval.

113. **PASS** — The remote URL is correct, if configured.
   Evidence: submission_audit.py checks; Git initial history and ignore rules; public metadata and anonymous HTTP 200; update pending approval.

114. **PASS** — All price calculations use the same price schedule.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

115. **PASS** — All token counts are taken from real API usage where required.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

116. **PASS** — Every model invocation, including retries or validation calls, is included in applicable cost accounting.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

117. **PASS** — Cached tokens are not double-charged as uncached tokens.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

118. **PASS** — Experiment configurations match their labels.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

119. **PASS** — All input documents correspond to the intended experiment.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

120. **PASS** — Practice accuracy calculations match the answer key.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

121. **PASS** — Defense results are not accidentally copied from attack results.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

122. **PASS** — Red-team reports match actual execution records.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

123. **PASS** — Exam results match final defended runs.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

124. **PASS** — The HTML report contains the same metrics as the underlying data.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

125. **PASS** — Running the agent again does not destroy previous logs.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

126. **PASS** — Running with defenses off does not silently activate any new defenses.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

127. **PASS** — No untrusted vendor document can directly authorize email sending or payment.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

128. **QUALIFIED** — All file paths are handled safely, and malicious document text cannot override system or developer instructions.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below. Verified for the documented scope; model behavior/visibility are not universally guaranteed, and new per-layer overhead is not separately measured.

129. **PASS** — The code contains no silent fallback to another model.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

130. **QUALIFIED** — The project can be reproduced from a fresh Git clone.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below. Verified for the documented scope; model behavior/visibility are not universally guaranteed, and new per-layer overhead is not separately measured.

131. **PASS** — Fix straightforward code, configuration, documentation, validation, and reporting problems.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

132. **PASS** — Preserve legitimate data, historical run records, and original attack evidence.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

133. **PASS** — Regenerate dependent reports from verified results when needed.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

134. **PASS** — Rerun only the necessary tests.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

135. **PASS** — If live API access is unavailable, report the missing verification instead of claiming a successful run.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

136. **PASS** — If correcting an issue requires significant API spending, explain the cost and request approval before triggering that expenditure.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

137. **PASS** — Never fabricate a passing result to fill a missing requirement.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

138. **PASS** — Do not alter the handbook, practice answer key, or exam documents to make tests pass.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

139. **PASS** — Do not change prices or usage counts merely to improve reported savings.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.

140. **PASS** — Verify every fix after applying it.
   Evidence: File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.
