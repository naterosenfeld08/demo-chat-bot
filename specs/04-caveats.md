# 04 - Caveats travel with the numbers

**Story:** As a researcher, I can't accidentally read more into a score than it supports.
**Backlog item:** #4
**Status:** draft

## What it does

After a run is loaded, some answers from `POST /api/ask` carry an interpretation
caveat. The caveat sentence is not written in Python. Each request reads
`data/caveats.json` from disk and appends the matching sentence to the answer
the server already computed.

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

## What it does NOT do

- Does not convert a composite, a ΔΔG value, or a Random Forest interval into
  Tm, activity, kcal/mol of experimental error, or any other unit.
- Does not let the language model choose, shorten, or rewrite a caveat. The
  server appends the file text.
- Does not add a caveat to the variant-count answer or the wall-clock answer.
  Feature #3's wording for those stays as it is.
- Does not add a caveat to "what was the best composite score". Only the
  stability question and the Tm refusal use the composite caveats.
- Does not invent a ΔΔG value or an interval when the loaded records do not
  have one. Missing stays "not recorded" by way of the existing unanswerable
  answer, and that answer cites no number, so it gets no caveat.
- Does not put caveats on the summary card.
- Does not compare two runs, draw a chart, or remember questions. Those are
  later backlog items.
- Does not read or modify the pipeline repository.

## Caveat file

Path: `data/caveats.json`, read on every ask. Four string keys:

| Key | Used when | Committed text |
|---|---|---|
| `fireprot_ddg` | An answer cites a ΔΔG value | `This value is a generic FireProt-scale prior, not a PETase-specific measurement.` |
| `composite_proxy` | The Tm refusal | `The composite is a proxy and does not predict Tm.` |
| `scores_not_tm` | After a composite comparison | `These scores are proxies, not measured Tm.` |
| `rf_interval` | An answer cites a Random Forest interval | `This interval is model disagreement, not experimental error.` |

The answer contains that exact string. If the file is missing, unreadable, or
the needed key is absent or not a string, the answer says the caveat is
`not recorded` and still obeys the rest of the rule: a Tm question still
returns no score, and no proxy is phrased as a measurement.

`app.config["CAVEATS_PATH"]` overrides the path so a test can point at a
temporary file. Unset, the path is `data/caveats.json` in the repo.

## Where the cited numbers come from

The design logs in `data/` do not contain ΔΔG or a Random Forest interval.
Those fields are optional on a variant record. Tests add them onto a copy of
a real record. A record without them is the normal sample run.

| Question shape | Number | Source |
|---|---|---|
| ΔΔG / ddG | `physics.ddg` on the same variant feature #3 calls the best composite, shown to three decimal places (half-up) | `log.jsonl` → `physics.ddg` |
| Tm | none | refusal uses `composite_proxy` |
| more stable than wild type | Best variant composite (mutation_count greater than 0) and the wild-type composite (the single record with mutation_count 0), each to three decimal places, plus the server-computed difference | `log.jsonl` → `physics.composite` for both |
| Random Forest interval / uncertainty | `physics.rf_low` and `physics.rf_high` on that same best-composite variant, each to three decimal places | `log.jsonl` → `physics.rf_low`, `physics.rf_high` |

Wild type means exactly one loaded design-log record whose `mutation_count` is
0. The sample runs have none. If there is not exactly one, the stability
question returns `the loaded run doesn't record that`, names a wild-type
record, includes no composite, and still appends `scores_not_tm` because the
question is asking for a stability reading.

ΔΔG and the interval are read from the best-composite variant only. If that
record lacks `physics.ddg`, or lacks either interval endpoint, the answer is
the feature #3 unanswerable answer, `facts` is empty, and no caveat is
appended. A missing endpoint is not filled with 0. The server does not turn a
standard deviation into an interval.

Displayed composites, ΔΔG values, interval endpoints, and the stability
difference use the same half-up three-decimal rule as feature #3. Exact values
may also appear in `facts`. The answer text uses the display form.

## HTTP contract

Same endpoint as feature #3: `POST /api/ask`, always `200`.

Tm refusal:

```json
{
  "answer": "The composite is a proxy and does not predict Tm.",
  "intent": "refuse_tm",
  "facts": {},
  "echo": null
}
```

The answer may contain only that sentence (the file text). It must not contain
a variant composite, a ΔΔG value, or an interval.

Stability, when both composites exist, has intent `stability_comparison`.
`facts` includes `best_composite`, `wild_type_composite`, `difference`, both
job ids, and `sources`. The answer states which composite is higher, or that
they are equal, then the `scores_not_tm` sentence.

ΔΔG has intent `ddg`. `facts` includes the value, the display string, the
`job_id`, and the source. The answer ends with the `fireprot_ddg` sentence.

Random Forest has intent `rf_interval`. `facts` includes both endpoints, both
display strings, the `job_id`, and the sources. The answer ends with the
`rf_interval` sentence.

In `LLM_MODE=echo`, `echo` is the JSON stats block and includes a `caveats`
object with the sentences actually attached on that request. A live model is
not required for any of this.

Questions feature #3 already answers (variant count, best composite, wall
clock, GDT-TS, nothing loaded) keep their current intents and do not gain a
caveat.

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

| # | Question | Answer |
|---|---|---|
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |

## Amendments

| Date | Change | Why |
|---|---|---|
|  |  |  |

## Notes

The sample design logs only store `physics.composite` and the other sequence
proxies. ΔΔG and the Random Forest interval live on the separate predictor
(`predict.py` in the pipeline), which this app does not run. The field names
`physics.ddg`, `physics.rf_low`, and `physics.rf_high` are a contract for this
app so a log that does carry them can be cited with provenance. They are not
a claim that today's CLI writes those keys.
