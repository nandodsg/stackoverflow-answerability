"""AC-0.11 check (no warehouse): every headline number on presentation/index.html equals its source.

A headline number is wrapped in an element with `data-num="<key>"`; NUMBERS below says, for each key, which committed
file it comes from and how it is rounded. The check fails when a page value differs from the recomputed one, when a
key on the page has no entry here (or an entry has no element on the page), or when a count-up's `data-count` would
animate to a different value than the text it replaces.

Second part, a warning only: every other number on the page that matches no source value and is not in the README is
listed, so a number typed by hand shows up for review. It never fails the run.

Sources: the exported marts (presentation/data/), the EDA caches (eda/*/output/), the BigQuery job log
(eda/d5_budget/output/jobs.csv), the labeling spend (eda/d6_labelers/output/, built from labels/spend_log.csv), the
seed of model labels, the dbt profile template, the specs and TESTING.md, and dbt's manifest. The manifest comes from
`dbt parse`, which needs no warehouse connection: run it first.

Run: dbt parse && python presentation/check_numbers.py
"""
import csv
import functools
import html.parser
import json
import math
import pathlib
import re
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "presentation" / "index.html"
EXCLUDED = set()  # ids of slides or dialogs not tagged yet (none now)
GiB = 2**30


# --- Sources ---------------------------------------------------------------------------------------------------

def read_csv(rel):
    """Rows of a committed CSV; the exported marts start with an attribution comment line."""
    lines = (ROOT / rel).read_text(encoding="utf-8").splitlines()
    return list(csv.DictReader(line for line in lines if not line.startswith("#")))


@functools.cache
def p1_tags_2022():
    return [r for r in read_csv("presentation/data/mart_p1_tags.csv") if r["creation_year"] == "2022"]


@functools.cache
def p2(tag, year):
    return next(r for r in read_csv("presentation/data/mart_p2_python_dbt.csv")
                if r["tag"] == tag and r["creation_year"] == str(year))


@functools.cache
def edits_2022():
    return next(r for r in read_csv("eda/d4_edits/output/edit_profile.csv")
                if r["segment"] == "all" and r["creation_year"] == "2022")


@functools.cache
def jobs():
    return read_csv("eda/d5_budget/output/jobs.csv")


@functools.cache
def labeler(model):
    return next(r for r in read_csv("eda/d6_labelers/output/labelers.csv") if r["model"] == model)


@functools.cache
def spend_by_route():
    totals = {}
    for r in read_csv("eda/d6_labelers/output/spend_by_stage.csv"):
        totals[r["route"]] = totals.get(r["route"], 0) + float(r["usd"])
    return totals


@functools.cache
def manifest():
    path = ROOT / "target" / "manifest.json"
    if not path.exists():
        sys.exit("target/manifest.json not found: run `dbt parse` first (it needs no warehouse connection)")
    return json.loads(path.read_text(encoding="utf-8"))


def dbt_tests():
    return [n for n in manifest()["nodes"].values() if n["resource_type"] == "test"]


def names_ac(node):
    """A test names its acceptance criterion in its meta, description, name or SQL (`AC-x.y`)."""
    fields = {k: node.get(k) for k in ("meta", "config", "description", "name", "raw_code", "tags")}
    return re.search(r"AC-\d", json.dumps(fields)) is not None


P3_LABELS = {"worked_example", "environment_dependent", "ask_scope", "code_focus", "failure_description",
             "image_only_evidence"}


@functools.cache
def p3_rows(mart):
    return read_csv(f"presentation/data/{mart}.csv")


def p3(feature, bucket, col="accepted_rate_effect", version="original", cohort="2018-2021"):
    """One value of a P3 effects or rates mart: the 2018-2021 pool on the original text, unless told otherwise."""
    kind = "label" if feature in P3_LABELS else "feature"
    mart = f"mart_p3_{kind}_{'rates' if col.endswith('rate') else 'effects'}"
    return float(next(r[col] for r in p3_rows(mart) if r["feature"] == feature and r["bucket"] == bucket
                      and r["version"] == version and r["cohort"] == cohort))


def rule_gaps():
    return [r for r in p3_rows("mart_p3_feature_effects") if r["version"] == "original" and r["cohort"] == "2018-2021"]


def p3_all_questions(col):
    """All 2018-2021 questions: the two buckets of `has_code_block` (plus its 'unknown') cover every question."""
    return sum(int(r[col]) for r in p3_rows("mart_p3_feature_rates") if r["feature"] == "has_code_block"
               and r["version"] == "original" and r["cohort"] == "2018-2021")


def incremental(label, level):
    return next(r for r in p3_rows("mart_p3_label_incremental") if r["label"] == label and r["level"] == level)


def vs_rules(label, level, rule, value, col):
    return float(next(r[col] for r in p3_rows("mart_p3_label_vs_rules") if r["label"] == label and r["level"] == level
                      and r["rule_feature"] == rule and r["rule_value"] == value))


def never_edited_max_move():
    """Largest move of an accepted-rate gap between the original text and never-edited questions, 2018-2021. The page
    gives the worked example's move as the difference of the two values it shows (+17.2 -> +19.6), so the gaps are
    rounded to a tenth of a point first: 2.4 (unrounded it is 2.46)."""
    moves = []
    for mart in ("mart_p3_feature_effects", "mart_p3_label_effects"):
        pool = [r for r in p3_rows(mart) if r["cohort"] == "2018-2021"]
        never = {(r["feature"], r["bucket"]): r for r in pool if r["version"] == "never_edited"}
        for r in pool:
            if r["version"] == "original" and (r["feature"], r["bucket"]) in never:
                moves.append(abs(round(float(never[r["feature"], r["bucket"]]["accepted_rate_effect"]) * 100, 1)
                                 - round(float(r["accepted_rate_effect"]) * 100, 1)))
    return max(moves)


def points(x):
    """A gap in points with its sign, as typeset on the page: 0.1718 -> '+17.2', -0.149 -> '−14.9'."""
    return f"{x * 100:+.1f}".replace("-", "−")


def ranked(rows, col, n):
    return sorted((r for r in rows if r[col]), key=lambda r: int(r[col]))[:n]


def acceptance_criteria():
    return re.findall(r"^- (AC-\d+\.\d+) ", "\n".join(p.read_text(encoding="utf-8")
                                                     for p in sorted((ROOT / "specs").glob("0*.md"))), re.M)


def billed(pred=lambda j: True):
    return sum(int(j["bytes_billed"] or 0) for j in jobs() if pred(j)) / GiB


def scan_read(node):
    """GiB billed by one build of a model (every run of it bills the same)."""
    return max(int(j["bytes_billed"]) for j in jobs() if j["dbt_node"] == f"model.so_answerability.{node}") / GiB


# --- Formats ---------------------------------------------------------------------------------------------------

def pct(x, d=1):
    """A share as the page prints it, without the % sign: 0.3048 -> '30.5'."""
    return f"{float(x) * 100:.{d}f}"


def num(x, d=0):
    return f"{float(x):,.{d}f}"


def signed(x):
    """A signed whole number with a real minus sign, as typeset on the page: '−17', '+21'."""
    return f"{x:+.0f}".replace("-", "−")


# --- Headline numbers, by slide --------------------------------------------------------------------------------
# key -> (source, function returning the exact text the tagged element must show)

NUMBERS = {
    # slide 3, the data and its traps
    "raw-top-max-questions": ("eda/d1_sample_size/output/summary.md, raw top and bottom 10 tables", lambda: num(max(
        int(n) for n in re.findall(r"^\| [^|]+ \| (\d+) \|",
                                   (ROOT / "eda/d1_sample_size/output/summary.md").read_text(encoding="utf-8")
                                   .split("### Top 10 tags by raw rate")[1].split("## ", 1)[0], re.M)))),
    "median-tag-questions": ("eda/d1_sample_size/output/tag_stats_2022.csv", lambda: num(statistics.median(
        int(r["n_questions"]) for r in read_csv("eda/d1_sample_size/output/tag_stats_2022.csv")))),
    "one-more-accepted-points": ("100 / the median tag's questions", lambda: num(100 / statistics.median(
        int(r["n_questions"]) for r in read_csv("eda/d1_sample_size/output/tag_stats_2022.csv")))),
    "edited-2022": ("eda/d4_edits/output/edit_profile.csv",
                    lambda: pct(int(edits_2022()["n_edited"]) / int(edits_2022()["n_questions"]), 0)),
    "edit-check-differences": ("eda/d4_edits/output/edit_profile.csv, n_edited - n_last_edit_date over every row",
                               lambda: num(sum(int(r["n_edited"]) - int(r["n_last_edit_date"])
                                               for r in read_csv("eda/d4_edits/output/edit_profile.csv")))),
    "edit-check-edited": ("eda/d4_edits/output/edit_profile.csv, n_edited over every row", lambda: num(sum(
        int(r["n_edited"]) for r in read_csv("eda/d4_edits/output/edit_profile.csv")))),
    "questions-in-snapshot": ("tests/assert_snapshot_unchanged.sql, expected posts_questions rows", lambda: num(int(
        re.search(r"'posts_questions' as source_table, (\d+)",
                  (ROOT / "tests/assert_snapshot_unchanged.sql").read_text(encoding="utf-8")).group(1)))),
    "q1-fresh-run-gib": ("TESTING.md, q1.sql row: run as delivered in a fresh sandbox", lambda: re.search(
        r"\| `q1\.sql` \|.*?\((\d+\.\d+) GiB billed", (ROOT / "TESTING.md").read_text(encoding="utf-8")).group(1)),
    "text-edit-after-answer-2022": ("eda/d4_edits/output/edit_profile.csv", lambda: pct(
        int(edits_2022()["n_text_edit_after_first_answer"]) / int(edits_2022()["n_questions"]), 0)),
    "tag-edit-after-answer-2022": ("eda/d4_edits/output/edit_profile.csv", lambda: pct(
        int(edits_2022()["n_tag_edit_after_first_answer"]) / int(edits_2022()["n_questions"]), 0)),
    "python-answer-rate-2022": ("mart_p2_python_dbt.csv", lambda: pct(p2("python", 2022)["answer_rate"])),
    "python-answer-rate-2021": ("mart_p2_python_dbt.csv", lambda: pct(p2("python", 2021)["answer_rate"])),
    "legacy-accepted-ids": ("manifest: assert_accepted_answer_belongs_to_question error_if", lambda: next(
        n["config"]["error_if"].lstrip(">") for n in dbt_tests()
        if n["name"] == "assert_accepted_answer_belongs_to_question")),
    # slide 4, decisions on the traps
    "floor": ("(1.96 x 0.5 / 0.05)^2 rounded up; no exported tag below it", lambda: num(
        math.ceil((1.96 * 0.5 / 0.05) ** 2)
        if min(int(r["n_questions"]) for r in p1_tags_2022()) >= math.ceil((1.96 * 0.5 / 0.05) ** 2) else -1)),
    "floor-formula": ("(1.96 x 0.5 / 0.05)^2", lambda: num((1.96 * 0.5 / 0.05) ** 2, 1)),
    "edited-accepted-2022": ("eda/d4_edits/output/edit_profile.csv", lambda: pct(
        (int(edits_2022()["n_accepted"]) - int(edits_2022()["n_accepted_never_edited"]))
        / int(edits_2022()["n_edited"]), 0)),
    "never-edited-accepted-2022": ("eda/d4_edits/output/edit_profile.csv", lambda: pct(
        int(edits_2022()["n_accepted_never_edited"]) / int(edits_2022()["n_never_edited"]), 0)),
    "post-history-read-gib": ("job log: int_post_history_scan", lambda: num(scan_read("int_post_history_scan"))),
    "python-answers-per-answered-2021": ("mart_p2_python_dbt.csv",
                                         lambda: num(p2("python", 2021)["answers_per_answered_question"], 2)),
    "python-answers-per-answered-2022": ("mart_p2_python_dbt.csv",
                                         lambda: num(p2("python", 2022)["answers_per_answered_question"], 2)),
    # slide 5, decisions on definitions
    "magento2-answer-rate": ("mart_p1_tags.csv", lambda: pct(
        next(r for r in p1_tags_2022() if r["tag"] == "magento2")["answer_rate"], 0)),
    "magento2-accepted-rate": ("mart_p1_tags.csv", lambda: pct(
        next(r for r in p1_tags_2022() if r["tag"] == "magento2")["accepted_rate"], 0)),
    "python-questions-per-answer-yoy-2022": ("mart_p2_python_dbt.csv", lambda: signed(
        (float(p2("python", 2022)["questions_per_answer"]) / float(p2("python", 2021)["questions_per_answer"]) - 1)
        * 100)),
    "python-answers-per-question-yoy-2022": ("mart_p2_python_dbt.csv",
                                             lambda: signed(float(p2("python", 2022)["answers_per_question_yoy_rel"])
                                                            * 100)),
    # slides 6 and 7, the stack and its spend
    "billed-gib": ("job log, every job", lambda: num(billed())),
    "october-quota-share": ("job log, October jobs / 1 TiB",
                            lambda: pct(billed(lambda j: j["creation_time"].startswith("2026-10")) / 1024, 0)),
    "october-gib": ("job log, October jobs", lambda: num(billed(lambda j: j["creation_time"].startswith("2026-10")))),
    "november-gib": ("job log, November jobs",
                     lambda: num(billed(lambda j: j["creation_time"].startswith("2026-11")))),
    "outside-dbt-gib": ("job log, jobs not run by dbt", lambda: num(billed(lambda j: j["from_dbt"] == "False"))),
    "dbt-models": ("manifest", lambda: num(sum(1 for n in manifest()["nodes"].values()
                                               if n["resource_type"] == "model"))),
    "dev-cap-gib": ("profiles.example.yml, dev target", lambda: num(int(re.findall(
        r"maximum_bytes_billed: (\d+)", (ROOT / "profiles.example.yml").read_text(encoding="utf-8"))[0]) / GiB)),
    "full-scan-cap-gib": ("profiles.example.yml, full_scan target", lambda: num(int(re.findall(
        r"maximum_bytes_billed: (\d+)", (ROOT / "profiles.example.yml").read_text(encoding="utf-8"))[1]) / GiB)),
    "labeled-questions": ("seeds/quality_labels_analysis.csv rows", lambda: num(len(
        read_csv("seeds/quality_labels_analysis.csv")))),
    # The README's total adds the three routes, each rounded to the cent (US$ 10.65); unrounded it is 10.655 (the D6
    # summary says both).
    "llm-usd-total": ("eda/d6_labelers/output/spend_by_stage.csv, routes rounded then added",
                      lambda: num(sum(round(v, 2) for v in spend_by_route().values()), 2)),
    "llm-usd-anthropic": ("spend_by_stage.csv", lambda: num(spend_by_route()["Anthropic API"], 2)),
    "llm-usd-vercel": ("spend_by_stage.csv", lambda: num(spend_by_route()["Vercel AI Gateway"], 2)),
    "llm-usd-jev": ("spend_by_stage.csv", lambda: num(spend_by_route()["TypeSafe API"], 2)),
    "jev-labels-usd": ("spend_by_stage.csv, the analysis-set stage", lambda: num(next(
        float(r["usd"]) for r in read_csv("eda/d6_labelers/output/spend_by_stage.csv")
        if r["stage"].startswith("5 ")), 2)),
    "jev-kappa": ("eda/d6_labelers/output/labelers.csv", lambda: num(labeler("jev-latest")["kappa_mean"], 2)),
    "jev-usd-per-question": ("labelers.csv", lambda: num(labeler("jev-latest")["usd_per_question"], 5)),
    "luna-kappa": ("labelers.csv", lambda: num(labeler("openai/gpt-6-luna")["kappa_mean"], 2)),
    "haiku-kappa": ("labelers.csv", lambda: num(labeler("claude-haiku-5-5")["kappa_mean"], 2)),
    # slide 8, tests and safeguards
    "body-read-gib": ("job log: int_question_body_scan", lambda: num(scan_read("int_question_body_scan"))),
    # slide 10, P1
    "p1-top10-accepted-low": ("mart_p1_tags.csv, 2022 top 10", lambda: pct(min(
        float(r["accepted_rate"]) for r in ranked(p1_tags_2022(), "rank_accepted_top", 10)))),
    "p1-top10-accepted-high": ("mart_p1_tags.csv, 2022 top 10", lambda: pct(max(
        float(r["accepted_rate"]) for r in ranked(p1_tags_2022(), "rank_accepted_top", 10)))),
    "p1-bottom10-accepted-low": ("mart_p1_tags.csv, 2022 bottom 10", lambda: pct(min(
        float(r["accepted_rate"]) for r in ranked(p1_tags_2022(), "rank_accepted_bottom", 10)))),
    "p1-bottom10-accepted-high": ("mart_p1_tags.csv, 2022 bottom 10", lambda: pct(max(
        float(r["accepted_rate"]) for r in ranked(p1_tags_2022(), "rank_accepted_bottom", 10)))),
    "accepted-rate-2022": ("eda/d4_edits/output/edit_profile.csv, all 2022 questions",
                           lambda: pct(int(edits_2022()["n_accepted"]) / int(edits_2022()["n_questions"]))),
    "p1-top3-accepted": ("mart_p1_tags.csv, ranks 1-3 by the lower bound", lambda: ", ".join(
        f"{r['tag']} {pct(r['accepted_rate'])}%" for r in ranked(p1_tags_2022(), "rank_accepted_top", 3))),
    "p1-top3-answers": ("mart_p1_tags.csv, ranks 1-3 by answers per question", lambda: ", ".join(
        f"{r['tag']} {num(r['answers_per_question'], 2)}" for r in ranked(p1_tags_2022(), "rank_answers_top", 3))),
    "p1-bottom1-accepted": ("mart_p1_tags.csv, bottom rank 1", lambda: "{tag} {v}%".format(
        tag=ranked(p1_tags_2022(), "rank_accepted_bottom", 1)[0]["tag"],
        v=pct(ranked(p1_tags_2022(), "rank_accepted_bottom", 1)[0]["accepted_rate"]))),
    "p1-bottom1-answers": ("mart_p1_tags.csv, bottom rank 1 by answers per question", lambda: "{tag} {v}".format(
        tag=ranked(p1_tags_2022(), "rank_answers_bottom", 1)[0]["tag"],
        v=num(ranked(p1_tags_2022(), "rank_answers_bottom", 1)[0]["answers_per_question"], 2))),
    # slide 11, P2, and its dialog
    "p2-python-apq-2013": ("mart_p2_python_dbt.csv", lambda: num(p2("python", 2013)["answers_per_question"], 2)),
    "p2-python-apq-2021": ("mart_p2_python_dbt.csv", lambda: num(p2("python", 2021)["answers_per_question"], 2)),
    "p2-python-apq-2022": ("mart_p2_python_dbt.csv", lambda: num(p2("python", 2022)["answers_per_question"], 2)),
    "p2-dbt-apq-2022": ("mart_p2_python_dbt.csv", lambda: num(p2("dbt", 2022)["answers_per_question"], 2)),
    "p2-python-apq-drop-per-year": ("mart_p2_python_dbt.csv, (2013 - 2021) / 8", lambda: num(
        (float(p2("python", 2013)["answers_per_question"]) - float(p2("python", 2021)["answers_per_question"])) / 8, 2)),
    "p2-python-accepted-2013": ("mart_p2_python_dbt.csv", lambda: pct(p2("python", 2013)["accepted_rate"])),
    "p2-python-accepted-2021": ("mart_p2_python_dbt.csv", lambda: pct(p2("python", 2021)["accepted_rate"])),
    "p2-python-accepted-2022": ("mart_p2_python_dbt.csv", lambda: pct(p2("python", 2022)["accepted_rate"])),
    "p2-python-accepted-drop-per-year": ("mart_p2_python_dbt.csv, (2013 - 2021) / 8, in points", lambda: pct(
        (float(p2("python", 2013)["accepted_rate"]) - float(p2("python", 2021)["accepted_rate"])) / 8)),
    "p2-python-accepted-drop-2022": ("mart_p2_python_dbt.csv, 2021 - 2022, in points", lambda: pct(
        float(p2("python", 2021)["accepted_rate"]) - float(p2("python", 2022)["accepted_rate"]))),
    "p2-python-among-answered-2021": ("mart_p2_python_dbt.csv",
                                      lambda: pct(p2("python", 2021)["accepted_rate_among_answered"])),
    "p2-python-among-answered-2022": ("mart_p2_python_dbt.csv",
                                      lambda: pct(p2("python", 2022)["accepted_rate_among_answered"])),
    "p2-python-among-answered-drop-2022": ("mart_p2_python_dbt.csv, 2021 - 2022, in points", lambda: pct(
        float(p2("python", 2021)["accepted_rate_among_answered"])
        - float(p2("python", 2022)["accepted_rate_among_answered"]))),
    "p2-python-questions-min": ("mart_p2_python_dbt.csv, python years", lambda: num(min(
        int(p2("python", y)["n_questions"]) for y in range(2013, 2023)))),
    "p2-python-questions-max": ("mart_p2_python_dbt.csv, python years", lambda: num(max(
        int(p2("python", y)["n_questions"]) for y in range(2013, 2023)))),
    "p2-dbt-questions-2020": ("mart_p2_python_dbt.csv", lambda: num(p2("dbt", 2020)["n_questions"])),
    "p2-dbt-questions-2021": ("mart_p2_python_dbt.csv", lambda: num(p2("dbt", 2021)["n_questions"])),
    "p2-dbt-questions-2022": ("mart_p2_python_dbt.csv", lambda: num(p2("dbt", 2022)["n_questions"])),
    "p2-rows": ("mart_p2_python_dbt.csv rows", lambda: num(len(read_csv("presentation/data/mart_p2_python_dbt.csv")))),
    "p2-python-qpa-2013": ("mart_p2_python_dbt.csv", lambda: num(p2("python", 2013)["questions_per_answer"], 2)),
    "p2-python-qpa-2022": ("mart_p2_python_dbt.csv", lambda: num(p2("python", 2022)["questions_per_answer"], 2)),
    "p2-python-apq-change-2022": ("mart_p2_python_dbt.csv", lambda: f'{float(
        p2("python", 2022)["answers_per_question_yoy_abs"]):+.2f}'.replace("-", "−")),
    "p2-python-exposure-low": ("mart_p2_python_dbt.csv, python years", lambda: pct(min(
        float(p2("python", y)["tag_exposure"]) for y in range(2013, 2023)))),
    "p2-python-exposure-high": ("mart_p2_python_dbt.csv, python years", lambda: pct(max(
        float(p2("python", y)["tag_exposure"]) for y in range(2013, 2023)))),
    "p2-dbt-exposure-high": ("mart_p2_python_dbt.csv, dbt years", lambda: pct(max(
        float(p2("dbt", y)["tag_exposure"]) for y in (2020, 2021, 2022)))),
    "p2-python-steps-down": ("mart_p2_python_dbt.csv: yearly steps whose intervals don't touch", lambda: num(sum(
        1 for y in range(2013, 2022) if float(p2("python", y + 1)["answers_per_question_upper"])
        < float(p2("python", y)["answers_per_question_lower"])))),
    "p2-mart-gib": ("job log: mart_p2_python_dbt", lambda: num(scan_read("mart_p2_python_dbt"), 2)),
    # slide 12, P3, and its dialog
    "p3-worked-accepted-yes": ("mart_p3_label_rates.csv", lambda: pct(p3("worked_example", "2: yes", "accepted_rate"))),
    "p3-worked-accepted-no": ("mart_p3_label_rates.csv", lambda: pct(p3("worked_example", "1: no", "accepted_rate"))),
    "p3-setup-accepted-yes": ("mart_p3_label_rates.csv",
                              lambda: pct(p3("environment_dependent", "2: yes", "accepted_rate"))),
    "p3-setup-accepted-no": ("mart_p3_label_rates.csv",
                             lambda: pct(p3("environment_dependent", "1: no", "accepted_rate"))),
    "p3-worked-gap": ("mart_p3_label_effects.csv", lambda: points(p3("worked_example", "2: yes"))),
    "p3-code-blocks-3-gap": ("mart_p3_feature_effects.csv", lambda: points(p3("code_block_count", "4: 3+"))),
    "p3-setup-gap": ("mart_p3_label_effects.csv", lambda: points(p3("environment_dependent", "2: yes"))),
    "p3-broad-ask-gap": ("mart_p3_label_effects.csv", lambda: points(p3("ask_scope", "2: broad"))),
    "p3-partial-code-gap": ("mart_p3_label_effects.csv", lambda: points(p3("code_focus", "2: partial"))),
    "p3-worked-answer-gap": ("mart_p3_label_effects.csv",
                             lambda: points(p3("worked_example", "2: yes", "answer_rate_effect"))),
    "p3-setup-answer-gap": ("mart_p3_label_effects.csv",
                            lambda: points(p3("environment_dependent", "2: yes", "answer_rate_effect"))),
    "p3-timing-max-gap": ("mart_p3_feature_effects.csv: hour, weekday, greeting", lambda: pct(max(
        abs(float(r["accepted_rate_effect"])) for r in rule_gaps()
        if r["feature"] in ("hour_posted_utc", "weekday_posted", "has_greeting_or_thanks")))),
    "p3-labeled-2018-2021": ("mart_p3_label_rates.csv, both levels of one label", lambda: num(sum(
        int(r["n_questions"]) for r in p3_rows("mart_p3_label_rates") if r["feature"] == "worked_example"
        and r["version"] == "original" and r["cohort"] == "2018-2021"))),
    "p3-questions": ("mart_p3_feature_rates.csv", lambda: num(p3_all_questions("n_questions"))),
    "p3-accepted-questions": ("mart_p3_feature_rates.csv", lambda: num(p3_all_questions("n_accepted"))),
    "p3-accepted-rate": ("mart_p3_feature_rates.csv",
                         lambda: pct(p3_all_questions("n_accepted") / p3_all_questions("n_questions"))),
    "p3-answer-rate": ("mart_p3_feature_rates.csv",
                       lambda: pct(p3_all_questions("n_answered") / p3_all_questions("n_questions"))),
    "p3-rule-gaps": ("mart_p3_feature_effects.csv", lambda: num(len(rule_gaps()))),
    "p3-rule-gaps-stable": ("mart_p3_feature_effects.csv", lambda: num(sum(
        r["accepted_rate_effect_stable"] == "True" for r in rule_gaps()))),
    "p3-rule-gaps-unstable": ("mart_p3_feature_effects.csv", lambda: num(sum(
        r["accepted_rate_effect_stable"] != "True" for r in rule_gaps()))),
    "p3-rule-gaps-unstable-max": ("mart_p3_feature_effects.csv", lambda: pct(max(
        abs(float(r["accepted_rate_effect"])) for r in rule_gaps() if r["accepted_rate_effect_stable"] != "True"))),
    "p3-floor-share-of-year": ("385 / a quarter of the labeled 2018-2021 questions", lambda: pct(
        math.ceil((1.96 * 0.5 / 0.05) ** 2) / (int(NUMBERS["p3-labeled-2018-2021"][1]().replace(",", "")) / 4), 0)),
    "p3-broad-ask-full-years": ("mart_p3_label_effects.csv", lambda: num(
        p3("ask_scope", "2: broad", "full_years_with_effect"))),
    "p3-worked-gap-inside-tags": ("mart_p3_label_effects.csv",
                                  lambda: points(p3("worked_example", "2: yes", "accepted_rate_effect_tag_adjusted"))),
    "p3-setup-gap-inside-tags": ("mart_p3_label_effects.csv", lambda: points(
        p3("environment_dependent", "2: yes", "accepted_rate_effect_tag_adjusted"))),
    "p3-code-block-gap": ("mart_p3_feature_effects.csv", lambda: points(p3("has_code_block", "2: yes"))),
    "p3-code-block-gap-inside-tags": ("mart_p3_feature_effects.csv",
                                      lambda: points(p3("has_code_block", "2: yes", "accepted_rate_effect_tag_adjusted"))),
    "p3-inside-tags-max-move": ("mart_p3_feature_effects.csv, rule gaps", lambda: pct(max(
        abs(float(r["accepted_rate_effect_tag_adjusted"]) - float(r["accepted_rate_effect"]))
        for r in rule_gaps() if r["accepted_rate_effect_tag_adjusted"]))),
    "p3-worked-with-code-block": ("mart_p3_label_vs_rules.csv", lambda: pct(
        vs_rules("worked_example", "2: yes", "has_code_block", "2: yes", "share_of_level"), 0)),
    "p3-code-block-worked": ("mart_p3_label_vs_rules.csv", lambda: pct(
        vs_rules("worked_example", "2: yes", "has_code_block", "2: yes", "share_of_rule_value"), 0)),
    "p3-setup-with-error-text": ("mart_p3_label_vs_rules.csv", lambda: pct(
        vs_rules("environment_dependent", "2: yes", "has_error_text", "2: yes", "share_of_level"), 0)),
    "p3-image-only-without-image": ("mart_p3_label_vs_rules.csv", lambda: pct(
        vs_rules("image_only_evidence", "2: yes", "has_image", "1: no", "share_of_level"), 0)),
    **{f"p3-kept-{key}": ("mart_p3_label_incremental.csv: rules-adjusted / raw gap", (lambda lab, lev: lambda: pct(
        float(incremental(lab, lev)["rules_adjusted_effect"]) / float(incremental(lab, lev)["raw_effect"]), 0))(
        lab, lev)) for key, lab, lev in [("worked", "worked_example", "2: yes"),
                                         ("setup", "environment_dependent", "2: yes"),
                                         ("partial-code", "code_focus", "2: partial"),
                                         ("broad-ask", "ask_scope", "2: broad"),
                                         ("multiple-asks", "ask_scope", "3: multiple"),
                                         ("image-only", "image_only_evidence", "2: yes")]},
    "p3-worked-gap-same-rules": ("mart_p3_label_incremental.csv",
                                 lambda: points(float(incremental("worked_example", "2: yes")["rules_adjusted_effect"]))),
    "p3-setup-gap-same-rules": ("mart_p3_label_incremental.csv", lambda: points(
        float(incremental("environment_dependent", "2: yes")["rules_adjusted_effect"]))),
    "p3-image-only-gap": ("mart_p3_label_effects.csv", lambda: points(p3("image_only_evidence", "2: yes"))),
    "p3-image-only-gap-same-rules": ("mart_p3_label_incremental.csv", lambda: points(
        float(incremental("image_only_evidence", "2: yes")["rules_adjusted_effect"]))),
    # The page gives the worked example's move as the difference of the two values it shows (+17.2 -> +19.6), so the
    # largest move is taken between rounded gaps: 2.4 (unrounded it is 2.46).
    "p3-never-edited-max-move": ("mart_p3_*_effects.csv, never-edited vs original, rounded gaps",
                                 lambda: num(never_edited_max_move(), 1)),
    "p3-worked-gap-never-edited": ("mart_p3_label_effects.csv",
                                   lambda: points(p3("worked_example", "2: yes", version="never_edited"))),
    "p3-code-block-gap-today": ("mart_p3_feature_effects.csv, current text",
                                lambda: points(p3("has_code_block", "2: yes", version="current"))),
    "p3-image-gap": ("mart_p3_feature_effects.csv", lambda: points(p3("has_image", "2: yes"))),
    "p3-image-gap-today": ("mart_p3_feature_effects.csv, current text",
                           lambda: points(p3("has_image", "2: yes", version="current"))),
    "p3-five-tags-among-answered": ("mart_p3_feature_effects.csv", lambda: points(
        p3("tag_count", "5: 5+", "accepted_rate_among_answered_effect"))),
    "p3-five-tags-among-answered-today": ("mart_p3_feature_effects.csv, current text", lambda: points(
        p3("tag_count", "5: 5+", "accepted_rate_among_answered_effect", version="current"))),
    "jev-kappa-label-low": ("labelers.csv, Jev's per-label kappas", lambda: num(min(
        float(v) for k, v in labeler("jev-latest").items() if k.startswith("kappa_") and k != "kappa_mean"), 2)),
    "jev-kappa-label-high": ("labelers.csv, Jev's per-label kappas", lambda: num(max(
        float(v) for k, v in labeler("jev-latest").items() if k.startswith("kappa_") and k != "kappa_mean"), 2)),
    # slide 13, quality and cost
    "dbt-tests": ("manifest: data tests + unit tests", lambda: num(len(dbt_tests()) + len(manifest()["unit_tests"]))),
    "dbt-tests-generic": ("manifest", lambda: num(sum(1 for n in dbt_tests() if n.get("test_metadata")))),
    "dbt-tests-singular": ("manifest", lambda: num(sum(1 for n in dbt_tests() if not n.get("test_metadata")))),
    "dbt-tests-unit": ("manifest", lambda: num(len(manifest()["unit_tests"]))),
    "dbt-tests-naming-ac": ("manifest: tests that name an AC-x.y", lambda: num(
        sum(names_ac(n) for n in dbt_tests()) + sum(names_ac(n) for n in manifest()["unit_tests"].values()))),
    "text-reads-gib": ("job log: full_scan target", lambda: num(billed(lambda j: j["dbt_target"] == "full_scan"))),
    # slide 14, limits
    "dbt-only-questions": ("mart_p2_python_dbt.csv, every dbt year", lambda: num(sum(
        int(r["n_questions"]) for r in read_csv("presentation/data/mart_p2_python_dbt.csv") if r["tag"] == "dbt"))),
    "text-sample-questions": ("labelers.csv: sample cost / cost per question, to the thousand", lambda: num(round(
        float(labeler("jev-latest")["usd_sample"]) / float(labeler("jev-latest")["usd_per_question"]), -3))),
    "text-sample-usd": ("labelers.csv", lambda: num(labeler("jev-latest")["usd_sample"])),
    # specs dialog
    "acceptance-criteria": ("specs/0*.md", lambda: num(len(acceptance_criteria()))),
    "acceptance-criteria-tested": ("TESTING.md: criteria whose kind is not EDA", lambda: num(sum(
        1 for ac in acceptance_criteria()
        if not re.search(rf"^\| {re.escape(ac)} \|.*\| EDA \|$", (ROOT / "TESTING.md").read_text(encoding="utf-8"),
                         re.M)))),
}


# --- The page --------------------------------------------------------------------------------------------------

class Page(html.parser.HTMLParser):
    """Collects the text of every `data-num` element and, outside the excluded ids, the page's visible text."""
    SKIP = {"script", "style", "template", "svg", "head"}
    VOID = {"br", "img", "input", "meta", "link", "hr", "source", "col", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []      # open tags: (tag, num key or None, excluded id or None, skipped)
        self.tagged = []     # (key, text, data-count, data-decimals, chapter)
        self.chunks = []     # (chapter, text) outside tagged elements
        self.chapter = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("section", "dialog") and a.get("id"):
            self.chapter = a["id"]
        if tag in self.VOID:
            return
        self.stack.append({"tag": tag, "num": a.get("data-num"), "text": [], "count": a.get("data-count"),
                           "decimals": a.get("data-decimals"), "skip": tag in self.SKIP})

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        while self.stack:
            el = self.stack.pop()
            if el["num"]:
                text = re.sub(r"\s+", " ", "".join(el["text"])).strip()
                self.tagged.append((el["num"], text, el["count"], el["decimals"], self.chapter))
            if el["tag"] == tag:
                break

    def handle_data(self, data):
        if any(el["skip"] for el in self.stack):
            return
        in_tag = False
        for el in self.stack:
            if el["num"]:
                el["text"].append(data)
                in_tag = True
        if not in_tag:
            self.chunks.append((self.chapter, data))


@functools.cache
def expected_value(key):
    return NUMBERS[key][1]()


def count_up_text(value, decimals):
    """What app.js's count-up ends on: toLocaleString('en-US') with fixed decimals."""
    return f"{float(value):,.{int(decimals or 0)}f}"


# --- The warning: numbers found in no source and not in the README ----------------------------------------------

NUMBER = re.compile(r"(?<![\w.\-/#])(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?![\w\-]|\.\d)")


def number_forms(value):
    """The ways the page prints a source value: a count as itself; a fraction at 1-3 decimals or as a share at 0-1."""
    if value.is_integer():
        return {f"{value:.0f}"}
    return {f"{value:.{d}f}" for d in (1, 2, 3)} | {f"{value * 100:.{d}f}" for d in (0, 1)}


@functools.cache
def known_numbers():
    """Values of the small CSVs (marts and EDA results) plus every number written in the README and the EDA summaries.
    The large EDA distributions (one row per tag) and the job log's raw byte counts are left out: they hold almost
    every whole number, so a typed number would always find a match there."""
    known = set()
    files = list((ROOT / "presentation" / "data").glob("*.csv")) + list(ROOT.glob("eda/*/output/*.csv"))
    for path in files:
        rows = read_csv(path.relative_to(ROOT))
        if path.parent.name == "output" and (len(rows) > 1000 or path.name == "jobs.csv"):
            continue
        for row in rows:
            for cell in row.values():
                try:
                    known |= number_forms(float(cell))
                except (TypeError, ValueError):
                    pass
    texts = [(ROOT / "README.md").read_text(encoding="utf-8")]
    texts += [p.read_text(encoding="utf-8") for p in ROOT.glob("eda/*/output/*.md")]
    for text in texts:
        for whole, frac in NUMBER.findall(text):
            known.add(whole.replace(",", "") + (frac or ""))
    return known


def unsourced(page, checked):
    """Page numbers outside tagged elements and the excluded slides that match nothing known (a value checked in a
    tagged element counts as known). Small counts (0-10), years and slide numbers are left out: they would only add
    noise."""
    known = known_numbers() | {w.replace(",", "") + f for text in checked for w, f in NUMBER.findall(text)}
    found = []
    for chapter, text in page.chunks:
        if chapter in EXCLUDED:
            continue
        for m in NUMBER.finditer(text):
            whole, frac = m.group(1).replace(",", ""), m.group(2) or ""
            value = float(whole + frac)
            if not frac and (value <= 10 or 1990 <= value <= 2030):
                continue
            if whole + frac not in known:
                start = max(0, m.start() - 30)
                found.append((chapter, m.group(0), re.sub(r"\s+", " ", text[start:m.end() + 20]).strip()))
    return found


# --- Run -------------------------------------------------------------------------------------------------------

def main():
    sys.stdout.reconfigure(encoding="utf-8")  # the page's minus signs and arrows, on a Windows console too
    page = Page()
    page.feed(PAGE.read_text(encoding="utf-8"))
    errors = []
    used = set()
    for key, text, count, decimals, chapter in page.tagged:
        used.add(key)
        if chapter in EXCLUDED:
            errors.append(f"{key} (#{chapter}): tagged on a slide this check leaves out; add it to the scope first")
        if key not in NUMBERS:
            errors.append(f"{key} (#{chapter}): no entry in NUMBERS")
            continue
        source, _ = NUMBERS[key]
        expected = expected_value(key)
        if text != expected:
            errors.append(f"{key} (#{chapter}): page says '{text}', {source} gives '{expected}'")
        if count is not None and count_up_text(count, decimals) != text.replace("−", "-"):
            errors.append(f"{key} (#{chapter}): data-count {count} animates to "
                          f"'{count_up_text(count, decimals)}', not '{text}'")
    for key in NUMBERS.keys() - used:
        errors.append(f"{key}: in NUMBERS but tagged nowhere on the page")

    warnings = unsourced(page, [expected_value(k) for k in NUMBERS])
    if warnings:
        print(f"warn: {len(warnings)} page numbers found in no source and not in the README (review, not a failure):")
        for chapter, value, context in warnings:
            print(f"  #{chapter}: {value}  ...{context}...")
    print("\n".join(errors) if errors else
          f"presentation numbers check passed: {len(page.tagged)} tagged numbers, {len(NUMBERS)} sources")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
