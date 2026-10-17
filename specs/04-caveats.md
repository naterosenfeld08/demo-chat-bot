# 04 - Caveats travel with the numbers

**Story:** As a researcher, I can't accidentally read more into a score than it supports.
**Backlog item:** #4
**Status:** questioned

## What it does

After a usable run is loaded, some answers from `POST /api/ask` carry an
interpretation caveat. The caveat sentence is not written in Python. Each
request reads `data/caveats.json` from disk and appends the matching sentence
to the answer the server already computed.

Four things change for the person asking:

- An answer that reports a ΔΔG value ends with the FireProt-scale caveat.
- Asking what Tm a variant will have is refused. The refusal says the composite
  is a proxy and does not predict Tm. It includes no score.
- Asking whether a variant is more stable than wild type returns a composite
  comparison computed by the server, then the sentence that these scores are
  proxies, not measured Tm.
- An answer that reports a Random Forest uncertainty interval ends with the
  sentence that the interval is model disagreement, not experimental error.

Editing `data/caveats.json` and asking again changes the next answer. No code
edit and no process restart.

Nothing loaded is still feature #3: every question, including Tm, asks for
`log.jsonl` or `run_summary.json` first. Intent `need_upload`, empty `facts`,
no refusal and no score.

## What it does NOT do

- Does not convert a composite, a ΔΔG value, or a Random Forest interval into
  Tm, activity, kcal/mol of experimental error, or any other unit.
- Does not let the language model choose, shorten, or rewrite a caveat. The
  server appends the file text.
- Does not add a caveat to the variant-count answer, the wall-clock answer, or
  "what was the best composite score". Feature #3's wording for those stays.
- Does not look up a `job_id` named in the question. "This variant" is always
  the best-composite variant from feature #3.
- Does not invent a ΔΔG value or an interval when the chosen record does not
  have a usable one. A missing value is not zero.
- Does not put caveats on the summary card.
- Does not compare two runs, draw a chart, or remember questions.
- Does not read or modify the pipeline repository.

## Which question is which

Checked only after a usable run is loaded, first match wins:

1. The whole word `tm` (so "estimate" and "atm" do not match) → Tm refusal.
2. The substring `wild` together with `stable` or `stability` → stability.
3. The substring `ddg`, `δδg`, `delta delta`, or `delta-delta` → ΔΔG.
4. The substring `uncertainty`, `random forest`, or `interval` → Random Forest.
5. Otherwise feature #3's existing order, unchanged.

A question that also says "variant", "composite", or "GDT" still follows this
order. Tm beats all of those.

## Caveat file

Path: `data/caveats.json`, read on every ask. Four string keys:

| Key | Used when | Committed text |
|---|---|---|
| `fireprot_ddg` | An answer cites a ΔΔG value | `This value is a generic FireProt-scale prior, not a PETase-specific measurement.` |
| `composite_proxy` | The Tm refusal | `The composite is a proxy and does not predict Tm.` |
| `scores_not_tm` | A stability answer, including when the comparison cannot be made | `These scores are proxies, not measured Tm.` |
| `rf_interval` | An answer cites a Random Forest interval | `This interval is model disagreement, not experimental error.` |

A caveat value is usable only when it is a string that contains something
other than spaces. If the file is missing, unreadable, or the needed key is
absent or not a usable string, a request that needed that key uses the
stand-in `not recorded` and still obeys the rest of the rule.

That stand-in is not appended to variant-count, best-composite, or wall-clock
answers. Those stay exactly as feature #3 wrote them.

For a Tm refusal with no usable `composite_proxy` text, `intent` is
`refuse_tm`, `facts` is `{}`, and `answer` is exactly `not recorded`.

`app.config["CAVEATS_PATH"]` overrides the path. Unset, the path is
`data/caveats.json` in the repo.

## Where the cited numbers come from

The design logs in `data/` do not contain ΔΔG or a Random Forest interval.
Those fields are optional. Tests add them onto a copy of a real record.

The chosen variant is the same winner feature #3 already uses for the best
composite. Its ΔΔG is that record's `physics.ddg` in the design log. Its
interval is that record's `physics.rf_low` and `physics.rf_high`. A `job_id`
typed in the question does not change the winner.

If both a run summary and a design log are loaded and they name different
winning `job_id`s, the answer still uses the feature #3 winner, and it
includes the sentence `run_summary.json and log.jsonl disagree on which variant is best.`
The ΔΔG or interval is read from that winning `job_id` in the log. If the log
has no such record, or the field is not usable, the answer is unanswerable,
cites no number, includes the disagreement sentence, and appends no FireProt
or interval caveat.

A numeric field is usable only under the same rule as the summary card: an
int or a finite float. `null`, a string (including `"0"` and `"-1.2"`), a
boolean, and NaN are missing. They are not coerced to zero.

Wild type is a design-log record whose `mutation_count` is numeric 0 (`0` or
`0.0`). A string `"0"` or a boolean is not a wild type. The comparison needs
exactly one wild-type record and at least one record with `mutation_count`
greater than 0, and both sides need a usable `physics.composite`. Otherwise
the stability answer is unanswerable: intent `unanswerable`, `facts` `{}`,
the sentence `the loaded run doesn't record that`, the name `log.jsonl`, and
the words `mutation_count` and `0`. It still appends `scores_not_tm` when that
text is usable, because the question is asking for a stability reading. It
does not include a composite.

Displayed scores use feature #3's half-up three-decimal rule, including
trailing zeros. The stability difference is the exact best-variant composite
minus the exact wild-type composite, then that same rounding. It is negative
when the wild-type composite is higher. The prose says who is higher by the
absolute display, or that the composites are equal. It does not subtract the
already-rounded displays.

## HTTP contract

Same endpoint as feature #3: `POST /api/ask`, always `200`.

Tm refusal, when the caveat text exists:

```json
{
  "answer": "The composite is a proxy and does not predict Tm.",
  "intent": "refuse_tm",
  "facts": {}
}
```

The answer is the file text alone. A number written in the question does not
appear in the answer. Neither does any composite, ΔΔG, or interval from the run.

Stability success, intent `stability_comparison`. `facts` is exactly:

- `best_composite`, `best_composite_display`
- `wild_type_composite`, `wild_type_composite_display`
- `difference`, `difference_display` (signed, best minus wild type)
- `best_job_id`, `wild_type_job_id`
- `sources`: `best_composite` and `wild_type_composite`, each
  `log.jsonl → physics.composite`

The answer includes both displays, both job ids, that source, then either
`The best variant composite is higher by <absolute display>.`,
`The wild-type composite is higher by <absolute display>.`, or
`The composites are equal.` Then the `scores_not_tm` sentence.

ΔΔG success, intent `ddg`. `facts` is exactly `ddg`, `ddg_display`, `job_id`,
`source`. `source` is `log.jsonl → physics.ddg`. The answer includes the
display, the job id, and that source, and ends with the `fireprot_ddg`
sentence.

Random Forest success, intent `rf_interval`. `facts` is exactly `rf_low`,
`rf_high`, `rf_low_display`, `rf_high_display`, `job_id`, `sources`.
`sources.rf_low` is `log.jsonl → physics.rf_low` and `sources.rf_high` is
`log.jsonl → physics.rf_high`. The answer includes both displays, the job id,
and both sources, and ends with the `rf_interval` sentence.

If the chosen record lacks a usable `physics.ddg`, or lacks either usable
interval endpoint, the answer is unanswerable: intent `unanswerable`, `facts`
`{}`, `the loaded run doesn't record that`, and `log.jsonl` plus the missing
field name (`physics.ddg`, `physics.rf_low`, or `physics.rf_high`). No caveat
is appended, and a present endpoint is not cited alone.

In `LLM_MODE=echo`, `echo` is the JSON stats block and includes `caveats`:

- sentences actually attached, keyed by the caveat name
- `{}` when this request attaches none, including feature #3 answers and a
  ΔΔG or interval question that cited no value
- `{"<key>": "not recorded"}` when this request needed that key and the text
  was missing

A live model is not required.

## Acceptance criteria

- [ ] It's done when any answer citing a ΔΔG value appends the FireProt-scale caveat text from `data/caveats.json`, and that text states the value is a generic prior and not a PETase-specific measurement.
- [ ] It's done when asking "what Tm will this variant have" returns a refusal that contains the `composite_proxy` text, states that the composite is a proxy and does not predict Tm, and returns no number.
- [ ] It's done when asking "is this variant more stable than wild type" returns the composite comparison (best variant versus the wild-type record) followed by the `scores_not_tm` sentence that these scores are proxies, not measured Tm.
- [ ] It's done when any answer citing a Random Forest uncertainty interval states that the interval is model disagreement, not experimental error, using the `rf_interval` text from the file.
- [ ] It's done when the caveat text is read at request time from `data/caveats.json`, so that editing that file changes the next answer without a code change or a restart.
- [ ] It's done when a loaded run has no `physics.ddg` and a ΔΔG question returns `the loaded run doesn't record that`, with empty `facts` and without the FireProt caveat.
- [ ] It's done when a Tm question includes a number in the wording, and that number does not appear in the refusal.
- [ ] It's done when the variant-count answer still does not include a caveat sentence.

## Question round

Human accepted the proposed answers on 2026-10-16. Agent 2 was Grok 4.6
because other model families were over the usage limit.

| # | Question | Answer |
|---|---|---|
| 1 | Which intent wins when one question matches several shapes? | Tm, then stability, then ΔΔG, then the interval, then feature #3. "variant" does not beat Tm. |
| 2 | What if nothing is loaded? | Still the upload prompt. No Tm refusal and no score. |
| 3 | Which wordings count, and does a named job id pick the variant? | Word rules are in "Which question is which". The variant is always the best-composite winner. A named job id is ignored. |
| 4 | What if the caveat file or a key is bad? | Tm stays `refuse_tm`, answer exactly `not recorded`, facts empty. Variant count, best composite, and wall clock are unchanged. |
| 5 | Not exactly one wild-type record? | Intent `unanswerable`, empty facts, names `log.jsonl` and a `mutation_count` of 0, and still appends `scores_not_tm` when that text exists. |
| 6 | Wild type or mutants lack a usable composite? | Same path as question 5. |
| 7 | Null, string, boolean, or NaN? | Missing. Not coerced to 0. Wild type is only numeric 0. |
| 8 | Summary and log disagree on the winner? | Keep feature #3's winner, say the two artifacts disagree, and read the field from that job in the log. If it is missing, unanswerable, no invented number. |
| 9 | Exact facts keys and echo caveats? | Listed under HTTP contract. Echo `caveats` holds only sentences actually attached, `{}` when none, and `not recorded` only for a key this request needed. |
| 10 | How is the stability difference rounded and signed? | Exact subtraction, then half-up to three decimals. Signed best minus wild type, so negative when wild type is higher. |

## Amendments

| Date | Change | Why |
|---|---|---|
|  |  |  |

## Notes

The sample design logs only store `physics.composite` and the other sequence
proxies. ΔΔG and the Random Forest interval live on the separate predictor in
the pipeline, which this app does not run. The field names `physics.ddg`,
`physics.rf_low`, and `physics.rf_high` are a contract for this app. They are
not a claim that today's CLI writes those keys.
