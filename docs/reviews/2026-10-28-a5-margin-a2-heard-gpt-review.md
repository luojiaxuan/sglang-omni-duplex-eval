# External review: A5 thinker speech budget and A2 Qwen3-Omni heard mapping (2026-10-28)

ChatGPT GPT-6, Pro, temporary chat, thought 13m44s. Attachments: my-judgment.md (my position written
before asking), a5_fit_output.txt, a5_fit.py, a5_corpus.jsonl, a5_draft.diff. Code read from
sgl-project/sglang-omni at ed09865a. Full reply below, as returned.

---

## Q1 — A5

Ship the runtime clamp, retain an affine envelope, and use m=1.5: 483 thinker tokens at a 4096-frame talker cap. Apply it only when the deployment and request actually generate speech; preserve the caller's smaller thinker limit and leave text-only requests unchanged. The draft's routing implements that distinction. Use a=600, b=4.405, not b=4.40. (a5_draft.diff:55–77,108–113,153–158.)

N_cap = min(N_requested, floor((C/m − a)/b))

The inversion is correct conditional on F(N) ≤ m(a+bN), compatible token/frame accounting, and a nonnegative feasible budget; fitting completed utterances does not establish that inequality for every subsequently truncated prefix. (a5_fit.py:23–34,69–75.)

The LP is a valid empirical affine majorant, not a physical "48-second startup cost." Its objective minimizes a + b*mean(n) subject to covering every observed point and b>=0; it does not identify a universally lowest line or establish extrapolation beyond the observed lengths. (a5_fit.py:37–53.)

The two reported supporting points, (240,1657) and (685,3617), imply a=599.9213483, b=4.404494382. Rounding to 600 + 4.40n predicts 1656 and 3614, missing those points by 1 and 3 frames; outward rounding to 600 + 4.405n preserves their coverage. (a5_fit_output.txt:14–15.)

A pure ratio is not intrinsically better: it assumes scale-invariant worst-case speech cost and gives away capacity on longer observed replies; the affine fit instead risks underestimating longer numeric-heavy replies because its asymptotic slope is only 4.4045. The observed maximum ratio is 1657/240 = 6.9041667, not a strict upper bound of 6.90; the script also excludes n<20 when reporting that maximum, so inspect short replies before declaring a ratio envelope. (a5_fit.py:62–64; a5_fit_output.txt:14.)

Choose m=1.5 as a capacity/reliability policy, not as a statistically certified failure rate. It provides 50% headroom over the fitted upper envelope and 47.3% more text than m=2; moving to m=2 removes another 32.1% of the available text budget without independent evidence quantifying the benefit. The supplied sweep reports the following; duration columns are arithmetic at the reported 3.69 frames/token. (a5_fit_output.txt:1–11.)

| Margin | Affine budget | Pure-ratio budget¹ | Reported held-out exceedances / 97 | Duration at 3.69 frames/token |
| --- | --- | --- | --- | --- |
| 1.0 | 793 | 593 | 1.87 | 234.1 s |
| 1.25 | 607 | 474 | 0.67 | 179.2 s |
| 1.5 | 483 | 395 | 0.03 | 142.6 s |
| 2.0 | 328 | 296 | 0.00 | 96.8 s |

¹Using r=1657/240; coverage of excluded short replies remains unverified.

#3157 supports the method, not automatic transfer of its margin: text_length_budget allocates more codec frames for already-known text as m increases; this inverse policy removes generated content as m increases. Its explicit caller limit also overrides the derived default, unlike the proposed cross-stage clamp. (qwen3_tts/request_builders.py:771–783; #3157.)

Do not merge the draft unchanged.

| Defect | Required change |
| --- | --- |
| ENVELOPE_A/B/NOTE remain placeholders. | Insert outward-rounded constants and document calibration scope. (a5_draft.diff:43–46.) |
| max(1, floor(...)) silently violates the claimed bound for small caps. | Reject an infeasible speech budget or define an explicit fallback; with the recommended constants and margin, even one token requires at least 907 frames under this envelope. (a5_draft.diff:55–63.) |
| A thinker length stop still produces truncation. | Do not claim this makes replies naturally complete: result() explicitly relays FINISH_LENGTH_KIND as REPLY_TRUNCATED. (thinker_session.py:393–433.) |
| Added tests only accommodate signature changes. | Add budget tests for both request/session paths, text-only, smaller explicit limits, raised talker caps, and infeasible caps; run paired audio tests measuring thinker-length, talker-length, and natural completion separately. (a5_draft.diff:161–248.) |

## Q2 — A2

There are two independent bugs: conditioning consumption is not acoustic alignment, and +3 counts the wrong rows. heard_tokens() returns 3 + floor(t/80), but build_assistant_part() identifies the first three rows as the chat-template prefix; prefill contains only one actual reply-text row, followed by a FIFO of later text rows. Neither three nor one should become automatically "heard" content at time zero. (thinker_session.py:86–87; components/talker_input.py:94–117,150–155.)

Ship corrected (a), substitute (d) only after verified natural audio completion, and require (c) before calling heard-prefix reconstruction accurate. The corpus contains utterance totals, not timestamped prefixes; it cannot validate a prefix-error guarantee. (a5_fit.py:23–34; my-judgment.md:51–61.)

| Option | Decision | Failure mode |
| --- | --- | --- |
| (a) Median r=3.69 | Immediate approximation; remove +3. | A median is not a mean-unbiased estimator; pauses, numeric expansion, markup and varying local pace produce over- and under-retention. Whole-utterance ratios do not substantiate "±20% per cut." |
| (b) Maximum r≈6.904 | Reject as the default and reject "never keeps unheard text." | A maximum whole-reply average does not bound every prefix's duration; initial silence or a locally slow passage still defeats it. At the median rate it retains only 53.4%, dropping 46.6%, before boundary effects. |
| (c) Forced alignment | Preferred timing-based implementation. | Not exact: model timing errors, text/audio mismatch and numeral-normalization offsets remain; extra model resources and latency are real costs. Aligning the entire future reply against truncated audio can fabricate tail boundaries. The existing worker already handles normalization and frame-end overshoot. (alignment_worker.py:82–156.) |
| (d) Reply-specific N/F | Prefer over (a) once complete text and naturally completed audio are available. | Corrects between-reply rate variation, not within-reply pace. Using the full transcript with a cancelled/capped/partially delivered duration can falsely retain the entire reply at the end of that partial audio. |

Use these provisional mappings, excluding EOS/control tokens from N:
h_a(t) = clamp(floor(t_ms / (80·3.69)), 0, N); h_d(t) = clamp(floor(N · t_ms / T_complete,ms), 0, N).

At 4033 ms, current code retains 53, your proposed (a) with +3 retains 16, and corrected (a) retains 13; those estimates must be checked against actual audio rather than accepted because one resembles an ASR word count. (my-judgment.md:44–49,52–53; thinker_session.py:86–87.)

Use reply-local played-audio time, not generated/delivered duration; enforce h(0)=0, bounds and monotone cuts; preserve the existing stale-KV/rebuild behavior. For alignment, map completed word/character ends back to the original generated token IDs; do not independently retokenize a prefix and assume identical IDs. (thinker_session.py:148–222; alignment_worker.py:82–156.)

## Data contradictions and limits

The corpus count is correct; its independence and collection uniformity are overstated. Independent JSONL recount: 224 = 193 completed + 28 null-status/error + 3 incomplete; the completed subset contains 88 prompt IDs and 126 distinct transcripts, not 193 independent text cases. The three incomplete records are at physical lines 210, 216, 220, each with 327.657 s and max_output_tokens; the JSONL does not record caps, voices, seeds or model revisions, so "all selected runs used 16384" is not independently auditable.

The split sweep is repeated internal validation, not 19,400 independent held-out observations. random.shuffle(points) splits rows, allowing identical transcripts and prompt families into both halves; neither zero exceedances at m=2 nor 0.03/97 at m=1.5 establishes a deployment failure probability. Split by prompt/text family, then test new voices and actual clamped generations; retain censored/error cases as a separate failure audit rather than fitting their truncated audio as completed speech. (a5_fit.py:66–75.)

The numeric-list case exposes substantial synthesis variability: identical transcripts at a5_corpus.jsonl:8,110 take 83.337 s versus 132.537 s, a 59.0% increase. The reported maximum whole-reply ratio is 87.1% above the median (6.90417/3.69−1), contradicting a blanket ±20% rate characterization—but not measuring prefix error, which this corpus lacks.

Two smaller numerical corrections: 328 tokens at 3.69 frames/token correspond to 96.8 s, not 90 s; the quoted ASR span contains 14 words, while Qwen2 pretokenization of the punctuated quote produces 15 pieces before BPE, so "14 model tokens" is not supported as written. (my-judgment.md:33–34,44–49; tokenization_qwen2.py:39.)

Reproduction boundary: corpus counts, duplicate structure and arithmetic above were independently checked; token ranges, median token ratios and the 200-split output remain supplied results because the tokenizer artifact/revision is absent. Add actual generated-token counts and codec-step counts to future records; a5_fit.py currently retokenizes transcripts and rounds audio_s/0.08, which is not the runtime accounting itself.
