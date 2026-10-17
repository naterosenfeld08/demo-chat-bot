"""Tests for specs/04-caveats.md. Written before that feature exists."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from conftest import SEED42, as_jsonl, design_log_records, payload, upload

FIREPROT = (
    "This value is a generic FireProt-scale prior, "
    "not a PETase-specific measurement."
)
PROXY = "The composite is a proxy and does not predict Tm."
NOT_TM = "These scores are proxies, not measured Tm."
RF_CAVEAT = "This interval is model disagreement, not experimental error."
DISAGREE = "run_summary.json and log.jsonl disagree on which variant is best."
STABILITY = "is this variant more stable than wild type"
BEST_JOB = "gen00002"


@pytest.fixture(autouse=True)
def echo_mode(app):
    app.config["LLM_MODE"] = "echo"


def ask(client, question: str):
    return payload(
        client.post(
            "/api/ask",
            json={"question": question},
            content_type="application/json",
        )
    )


def caveats_of(data) -> dict:
    echoed = json.loads(data["echo"])
    assert "caveats" in echoed
    return echoed["caveats"]


def committed_caveats() -> dict:
    return {
        "fireprot_ddg": FIREPROT,
        "composite_proxy": PROXY,
        "scores_not_tm": NOT_TM,
        "rf_interval": RF_CAVEAT,
    }


def use_caveats(app, tmp_path: Path, text: dict | None = None) -> Path:
    path = tmp_path / "caveats.json"
    path.write_text(json.dumps(text if text is not None else committed_caveats()), encoding="utf-8")
    app.config["CAVEATS_PATH"] = str(path)
    return path


def records() -> list[dict]:
    return design_log_records()


def best_composite(rows: list[dict]) -> float:
    for record in rows:
        if record.get("job_id") == BEST_JOB:
            return record["physics"]["composite"]
    raise AssertionError(f"{BEST_JOB} missing from the fixture")


def with_wild_type(rows: list[dict], composite, job_id: str = "wt") -> list[dict]:
    wild = copy.deepcopy(rows[0])
    wild["job_id"] = job_id
    wild["mutations"] = []
    wild["physics"]["mutation_count"] = 0
    wild["physics"]["composite"] = composite
    return rows + [wild]


def put(rows: list[dict], job_id: str, **physics) -> None:
    for record in rows:
        if record.get("job_id") == job_id:
            record["physics"].update(physics)
            return
    raise AssertionError(f"{job_id} missing from the fixture")


def summary_bytes() -> bytes:
    return (SEED42 / "run_summary.json").read_bytes()


def test_ddg_answer_appends_the_fireprot_caveat(client, app, tmp_path):
    """An answer that cites a ΔΔG value ends with the FireProt sentence from
    the caveat file, and names the log field it came from."""
    use_caveats(app, tmp_path)
    rows = records()
    put(rows, BEST_JOB, ddg=-1.2)
    upload(client, ("log.jsonl", as_jsonl(rows)))
    data = ask(client, "what is the ddG")
    assert data["intent"] == "ddg"
    assert data["answer"].endswith(FIREPROT)
    assert "generic" in data["answer"]
    assert "not a PETase-specific measurement" in data["answer"]
    assert "-1.200" in data["answer"]
    assert BEST_JOB in data["answer"]
    assert "log.jsonl → physics.ddg" in data["answer"]
    assert data["facts"] == {
        "ddg": pytest.approx(-1.2),
        "ddg_display": "-1.200",
        "job_id": BEST_JOB,
        "source": "log.jsonl → physics.ddg",
    }
    assert caveats_of(data) == {"fireprot_ddg": FIREPROT}


@pytest.mark.parametrize(
    "question",
    [
        "what is the ΔΔG",
        "what is the delta delta G",
        "what is the delta-delta G",
    ],
)
def test_ddg_wordings_cite_the_same_value(client, app, tmp_path, question):
    """Other ways of asking for ΔΔG cite the same value and the same caveat."""
    use_caveats(app, tmp_path)
    rows = records()
    put(rows, BEST_JOB, ddg=-1.2)
    upload(client, ("log.jsonl", as_jsonl(rows)))
    data = ask(client, question)
    assert data["intent"] == "ddg"
    assert data["answer"].endswith(FIREPROT)
    assert data["facts"]["ddg_display"] == "-1.200"
    assert data["facts"]["job_id"] == BEST_JOB


def test_named_job_does_not_pick_a_different_variant(client, app, tmp_path):
    """A job id written in the question is ignored. The cited ΔΔG belongs to
    the best-composite variant."""
    use_caveats(app, tmp_path)
    rows = records()
    put(rows, "gen00000", ddg=-5.5)
    put(rows, BEST_JOB, ddg=-1.2)
    upload(client, ("log.jsonl", as_jsonl(rows)))
    data = ask(client, "what is the ddG of gen00000")
    assert data["intent"] == "ddg"
    assert data["facts"]["job_id"] == BEST_JOB
    assert data["facts"]["ddg_display"] == "-1.200"
    assert "-5.500" not in data["answer"]
    assert "gen00000" not in data["answer"]


def test_tm_refusal_has_the_proxy_sentence_and_no_number(client, app, tmp_path):
    """Asking what Tm a variant will have, even with a number and the word
    variant in the question, returns only the proxy sentence."""
    use_caveats(app, tmp_path)
    upload(client, ("log.jsonl", as_jsonl(records())))
    data = ask(client, "what Tm will this variant have, was it 0.609 or 99.5?")
    assert data["intent"] == "refuse_tm"
    assert data["facts"] == {}
    assert data["answer"] == PROXY
    assert "0.609" not in data["answer"]
    assert "99.5" not in data["answer"]
    assert "8" not in data["answer"]
    assert caveats_of(data) == {"composite_proxy": PROXY}


def test_tm_beats_a_gdt_question(client, app, tmp_path):
    """A question that asks for Tm and GDT is still the Tm refusal."""
    use_caveats(app, tmp_path)
    upload(client, ("log.jsonl", as_jsonl(records())))
    data = ask(client, "what Tm and the GDT-TS of this variant")
    assert data["intent"] == "refuse_tm"
    assert data["answer"] == PROXY
    assert data["facts"] == {}
    assert "benchmark" not in data["answer"]


def test_atm_is_not_a_tm_question(client, app, tmp_path):
    """The letters tm inside another word do not refuse the question."""
    use_caveats(app, tmp_path)
    upload(client, ("run_summary.json", summary_bytes()))
    data = ask(client, "what does atm mean for this variant")
    assert data["intent"] == "n_variants"
    assert "8" in data["answer"]
    assert PROXY not in data["answer"]
    assert caveats_of(data) == {}


def test_tm_before_upload_still_asks_for_a_file(client, app, tmp_path):
    """A Tm question with nothing loaded asks for an upload and does not refuse."""
    use_caveats(app, tmp_path)
    data = ask(client, "what Tm will this variant have")
    assert data["intent"] == "need_upload"
    assert data["facts"] == {}
    assert "log.jsonl" in data["answer"]
    assert "run_summary.json" in data["answer"]
    assert PROXY not in data["answer"]
    assert caveats_of(data) == {}


def test_stability_comparison_then_the_proxy_sentence(client, app, tmp_path):
    """Asking whether this variant is more stable than wild type returns the
    best composite, the wild-type composite, a server-computed difference,
    and then the proxy sentence."""
    use_caveats(app, tmp_path)
    rows = with_wild_type(records(), 0.5)
    upload(client, ("log.jsonl", as_jsonl(rows)))
    data = ask(client, STABILITY)
    assert data["intent"] == "stability_comparison"
    assert data["answer"].endswith(NOT_TM)
    assert "0.609" in data["answer"]
    assert "0.500" in data["answer"]
    assert "The best variant composite is higher by 0.109." in data["answer"]
    assert BEST_JOB in data["answer"]
    assert "wt" in data["answer"]
    assert "log.jsonl → physics.composite" in data["answer"]
    facts = data["facts"]
    assert facts["best_composite"] == pytest.approx(best_composite(rows))
    assert facts["best_composite_display"] == "0.609"
    assert facts["wild_type_composite"] == pytest.approx(0.5)
    assert facts["wild_type_composite_display"] == "0.500"
    assert facts["difference"] == pytest.approx(best_composite(rows) - 0.5)
    assert facts["difference_display"] == "0.109"
    assert facts["best_job_id"] == BEST_JOB
    assert facts["wild_type_job_id"] == "wt"
    assert facts["sources"] == {
        "best_composite": "log.jsonl → physics.composite",
        "wild_type_composite": "log.jsonl → physics.composite",
    }
    assert set(facts) == {
        "best_composite",
        "best_composite_display",
        "wild_type_composite",
        "wild_type_composite_display",
        "difference",
        "difference_display",
        "best_job_id",
        "wild_type_job_id",
        "sources",
    }
    assert caveats_of(data) == {"scores_not_tm": NOT_TM}


def test_difference_is_negative_when_wild_type_is_higher(client, app, tmp_path):
    """When the wild-type composite is higher, the stored difference is
    negative and the sentence says the wild type is higher."""
    use_caveats(app, tmp_path)
    rows = records()
    exact = best_composite(rows)
    rows = with_wild_type(rows, 0.9)
    upload(client, ("log.jsonl", as_jsonl(rows)))
    data = ask(client, STABILITY)
    assert data["facts"]["difference"] == pytest.approx(exact - 0.9)
    assert data["facts"]["difference_display"] == "-0.291"
    assert "The wild-type composite is higher by 0.291." in data["answer"]
    assert data["answer"].endswith(NOT_TM)


def test_equal_composites_say_they_are_equal(client, app, tmp_path):
    """Equal composites are reported as equal, with a signed difference of zero."""
    use_caveats(app, tmp_path)
    rows = records()
    rows = with_wild_type(rows, best_composite(rows))
    upload(client, ("log.jsonl", as_jsonl(rows)))
    data = ask(client, STABILITY)
    assert "The composites are equal." in data["answer"]
    assert data["facts"]["difference_display"] == "0.000"
    assert data["facts"]["difference"] == pytest.approx(0.0)
    assert data["answer"].endswith(NOT_TM)


def test_stability_without_a_wild_type_record(client, app, tmp_path):
    """The sample run has no wild-type record. The answer cites no composite
    and still carries the proxy sentence."""
    use_caveats(app, tmp_path)
    upload(client, ("log.jsonl", as_jsonl(records())))
    data = ask(client, STABILITY)
    assert data["intent"] == "unanswerable"
    assert data["facts"] == {}
    assert "the loaded run doesn't record that" in data["answer"]
    assert "log.jsonl" in data["answer"]
    assert "physics.mutation_count" in data["answer"]
    assert data["answer"].endswith(NOT_TM)
    assert "0.609" not in data["answer"]
    assert caveats_of(data) == {"scores_not_tm": NOT_TM}


def test_two_wild_type_records_are_not_silently_picked(client, app, tmp_path):
    """Two wild-type records produce no comparison and no chosen winner."""
    use_caveats(app, tmp_path)
    rows = with_wild_type(records(), 0.5, job_id="wt-a")
    rows = with_wild_type(rows, 0.4, job_id="wt-b")
    upload(client, ("log.jsonl", as_jsonl(rows)))
    data = ask(client, STABILITY)
    assert data["intent"] == "unanswerable"
    assert data["facts"] == {}
    assert "0.609" not in data["answer"]
    assert "0.500" not in data["answer"]
    assert data["answer"].endswith(NOT_TM)


def test_string_zero_mutation_count_is_not_wild_type(client, app, tmp_path):
    """A mutation count of the string 0 is not a wild-type record."""
    use_caveats(app, tmp_path)
    rows = records()
    put(rows, "gen00000", mutation_count="0")
    upload(client, ("log.jsonl", as_jsonl(rows)))
    data = ask(client, STABILITY)
    assert data["intent"] == "unanswerable"
    assert data["facts"] == {}
    assert "0.609" not in data["answer"]


def test_missing_wild_type_composite_cites_no_number(client, app, tmp_path):
    """A wild-type record with no usable composite does not invent one."""
    use_caveats(app, tmp_path)
    rows = with_wild_type(records(), None)
    upload(client, ("log.jsonl", as_jsonl(rows)))
    data = ask(client, STABILITY)
    assert data["intent"] == "unanswerable"
    assert data["facts"] == {}
    assert "0.609" not in data["answer"]
    assert "0.000" not in data["answer"]
    assert data["answer"].endswith(NOT_TM)


def test_no_mutant_composite_cites_no_number(client, app, tmp_path):
    """If every mutated record lacks a composite, the wild-type number is not
    shown on its own."""
    use_caveats(app, tmp_path)
    rows = records()
    for record in rows:
        record["physics"]["composite"] = None
    rows = with_wild_type(rows, 0.5)
    upload(client, ("log.jsonl", as_jsonl(rows)))
    data = ask(client, STABILITY)
    assert data["intent"] == "unanswerable"
    assert data["facts"] == {}
    assert "0.500" not in data["answer"]
    assert data["answer"].endswith(NOT_TM)


def test_rf_interval_appends_the_model_disagreement_sentence(client, app, tmp_path):
    """An answer that cites a Random Forest interval ends with the sentence
    that it is model disagreement, not experimental error."""
    use_caveats(app, tmp_path)
    rows = records()
    put(rows, BEST_JOB, rf_low=0.1, rf_high=0.2)
    upload(client, ("log.jsonl", as_jsonl(rows)))
    data = ask(client, "what is the random forest uncertainty")
    assert data["intent"] == "rf_interval"
    assert data["answer"].endswith(RF_CAVEAT)
    assert "model disagreement" in data["answer"]
    assert "not experimental error" in data["answer"]
    assert "0.100" in data["answer"]
    assert "0.200" in data["answer"]
    assert BEST_JOB in data["answer"]
    assert "log.jsonl → physics.rf_low" in data["answer"]
    assert "log.jsonl → physics.rf_high" in data["answer"]
    assert data["facts"]["rf_low"] == pytest.approx(0.1)
    assert data["facts"]["rf_high"] == pytest.approx(0.2)
    assert data["facts"]["rf_low_display"] == "0.100"
    assert data["facts"]["rf_high_display"] == "0.200"
    assert data["facts"]["job_id"] == BEST_JOB
    assert data["facts"]["sources"] == {
        "rf_low": "log.jsonl → physics.rf_low",
        "rf_high": "log.jsonl → physics.rf_high",
    }
    assert caveats_of(data) == {"rf_interval": RF_CAVEAT}


def test_interval_wording_beats_the_word_composite(client, app, tmp_path):
    """A question that says both interval and composite cites the interval."""
    use_caveats(app, tmp_path)
    rows = records()
    put(rows, BEST_JOB, rf_low=0.1, rf_high=0.2)
    upload(client, ("log.jsonl", as_jsonl(rows)))
    data = ask(client, "what is the uncertainty of the composite")
    assert data["intent"] == "rf_interval"
    assert data["facts"]["rf_low_display"] == "0.100"
    assert data["answer"].endswith(RF_CAVEAT)


def test_recorded_zero_interval_is_cited(client, app, tmp_path):
    """A recorded interval of zero is a real value, not a missing one."""
    use_caveats(app, tmp_path)
    rows = records()
    put(rows, BEST_JOB, rf_low=0, rf_high=0)
    upload(client, ("log.jsonl", as_jsonl(rows)))
    data = ask(client, "what is the uncertainty")
    assert data["intent"] == "rf_interval"
    assert data["facts"]["rf_low_display"] == "0.000"
    assert data["facts"]["rf_high_display"] == "0.000"
    assert data["answer"].endswith(RF_CAVEAT)


def test_one_missing_interval_endpoint_is_not_cited(client, app, tmp_path):
    """An interval with only one endpoint is not filled in with zero and gets
    no interval caveat."""
    use_caveats(app, tmp_path)
    rows = records()
    put(rows, BEST_JOB, rf_low=0.1)
    upload(client, ("log.jsonl", as_jsonl(rows)))
    data = ask(client, "what is the random forest interval")
    assert data["intent"] == "unanswerable"
    assert data["facts"] == {}
    assert "the loaded run doesn't record that" in data["answer"]
    assert "log.jsonl" in data["answer"]
    assert "physics.rf_high" in data["answer"]
    assert "0.100" not in data["answer"]
    assert "0.000" not in data["answer"]
    assert RF_CAVEAT not in data["answer"]
    assert caveats_of(data) == {}


def test_editing_the_caveat_file_changes_the_next_answer(client, app, tmp_path):
    """Rewriting the caveat file between two requests changes the next answer
    without restarting the app."""
    text = committed_caveats()
    path = use_caveats(app, tmp_path, text)
    upload(client, ("log.jsonl", as_jsonl(records())))
    text["composite_proxy"] = "CAVEAT ALPHA"
    path.write_text(json.dumps(text), encoding="utf-8")
    first = ask(client, "what Tm will this variant have")
    assert first["answer"] == "CAVEAT ALPHA"
    text["composite_proxy"] = "CAVEAT BETA"
    path.write_text(json.dumps(text), encoding="utf-8")
    second = ask(client, "what Tm will this variant have")
    assert second["answer"] == "CAVEAT BETA"
    assert "CAVEAT ALPHA" not in second["answer"]


def test_default_caveat_file_supplies_the_committed_sentence(client):
    """With no path override, the Tm refusal uses the sentence committed in
    data/caveats.json."""
    upload(client, ("log.jsonl", as_jsonl(records())))
    data = ask(client, "what Tm will this variant have")
    assert data["intent"] == "refuse_tm"
    assert data["answer"] == PROXY


def test_missing_caveat_file_stands_in_not_recorded(client, app, tmp_path):
    """A missing caveat file makes the Tm answer exactly 'not recorded' and
    leaves the variant-count answer alone."""
    app.config["CAVEATS_PATH"] = str(tmp_path / "missing.json")
    upload(client, ("run_summary.json", summary_bytes()))
    refused = ask(client, "what Tm will this variant have")
    assert refused["intent"] == "refuse_tm"
    assert refused["answer"] == "not recorded"
    assert refused["facts"] == {}
    assert caveats_of(refused) == {"composite_proxy": "not recorded"}
    counted = ask(client, "how many variants were in this run")
    assert counted["intent"] == "n_variants"
    assert "8" in counted["answer"]
    assert "not recorded" not in counted["answer"]
    assert caveats_of(counted) == {}


def test_blank_caveat_text_is_not_recorded(client, app, tmp_path):
    """A blank caveat string is treated as missing."""
    text = committed_caveats()
    text["composite_proxy"] = "   "
    use_caveats(app, tmp_path, text)
    upload(client, ("log.jsonl", as_jsonl(records())))
    data = ask(client, "what Tm will this variant have")
    assert data["answer"] == "not recorded"
    assert data["intent"] == "refuse_tm"
    assert caveats_of(data) == {"composite_proxy": "not recorded"}


def test_ddg_missing_from_the_run_cites_nothing(client, app, tmp_path):
    """The sample run has no ΔΔG. The answer says so, names the log field,
    and does not attach the FireProt caveat."""
    use_caveats(app, tmp_path)
    upload(client, ("log.jsonl", as_jsonl(records())))
    data = ask(client, "what is the ddG")
    assert data["intent"] == "unanswerable"
    assert data["facts"] == {}
    assert "the loaded run doesn't record that" in data["answer"]
    assert "log.jsonl" in data["answer"]
    assert "physics.ddg" in data["answer"]
    assert FIREPROT not in data["answer"]
    assert caveats_of(data) == {}


@pytest.mark.parametrize("bad", [None, "0", "-1.2", True, float("nan")])
def test_unusable_ddg_is_not_coerced_to_zero(client, app, tmp_path, bad):
    """A null, string, boolean, or non-finite ΔΔG is missing, not a number."""
    use_caveats(app, tmp_path)
    rows = records()
    put(rows, BEST_JOB, ddg=bad)
    upload(client, ("log.jsonl", as_jsonl(rows)))
    data = ask(client, "what is the ddG")
    assert data["intent"] == "unanswerable"
    assert data["facts"] == {}
    assert FIREPROT not in data["answer"]
    assert "0.000" not in data["answer"]
    assert "-1.200" not in data["answer"]
    assert "-1.2" not in data["answer"]
    assert caveats_of(data) == {}


def test_summary_and_log_disagreement_is_stated(client, app, tmp_path):
    """When the summary and the log crown different variants, the answer says
    so and still cites the summary winner's ΔΔG from the log."""
    use_caveats(app, tmp_path)
    rows = records()
    put(rows, "gen00001", composite=0.99)
    put(rows, BEST_JOB, ddg=-1.2)
    upload(
        client,
        ("run_summary.json", summary_bytes()),
        ("log.jsonl", as_jsonl(rows)),
    )
    data = ask(client, "what is the ddG")
    assert data["intent"] == "ddg"
    assert DISAGREE in data["answer"]
    assert data["facts"]["job_id"] == BEST_JOB
    assert data["facts"]["ddg_display"] == "-1.200"
    assert data["answer"].endswith(FIREPROT)


def test_disagreement_with_no_ddg_invents_no_number(client, app, tmp_path):
    """If the artifacts disagree and the winning log record has no ΔΔG, the
    answer states the disagreement and cites no number and no FireProt caveat."""
    use_caveats(app, tmp_path)
    rows = records()
    put(rows, "gen00001", composite=0.99)
    upload(
        client,
        ("run_summary.json", summary_bytes()),
        ("log.jsonl", as_jsonl(rows)),
    )
    data = ask(client, "what is the ddG")
    assert data["intent"] == "unanswerable"
    assert data["facts"] == {}
    assert DISAGREE in data["answer"]
    assert "the loaded run doesn't record that" in data["answer"]
    assert FIREPROT not in data["answer"]
    assert "-1.200" not in data["answer"]
    assert caveats_of(data) == {}


def test_variant_count_does_not_include_a_caveat(client, app, tmp_path):
    """The variant-count answer stays free of every caveat sentence."""
    use_caveats(app, tmp_path)
    upload(client, ("run_summary.json", summary_bytes()))
    data = ask(client, "how many variants were in this run")
    assert data["intent"] == "n_variants"
    assert "8" in data["answer"]
    assert "run_summary.json" in data["answer"]
    for sentence in (FIREPROT, PROXY, NOT_TM, RF_CAVEAT):
        assert sentence not in data["answer"]
    assert caveats_of(data) == {}


def test_best_composite_question_does_not_gain_a_caveat(client, app, tmp_path):
    """Asking for the best composite score still returns that score with no
    caveat sentence."""
    use_caveats(app, tmp_path)
    upload(client, ("log.jsonl", as_jsonl(records())))
    data = ask(client, "what was the best composite score")
    assert data["intent"] == "best_composite"
    assert "0.609" in data["answer"]
    assert BEST_JOB in data["answer"]
    assert PROXY not in data["answer"]
    assert NOT_TM not in data["answer"]
    assert caveats_of(data) == {}
