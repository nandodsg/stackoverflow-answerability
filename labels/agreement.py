"""Agreement between two labelers on a gold set (specs/003, "Quality labels").

  python labels/agreement.py --set practice --model google/gemini-4-argon                 # hand labels vs a model
  python labels/agreement.py --set scoring --model spacexai/grok-4.7 --against google/gemini-4-argon
  python labels/agreement.py --set scoring --model claude-haiku-5-5 --against reviewed                 # a candidate

Per label: questions compared, raw agreement, Cohen's kappa (agreement corrected for what two labelers would reach by
chance with the same level frequencies; 0 = chance, 1 = perfect) and how often each labeler used each level. Then
every disagreement with the hand note and the models' reasons. `not_applicable` counts as a level: deciding whether a
label applies is part of the judgment. Labels made on an earlier rubric version are mapped to the current levels
first (LEGACY below). Writes labels/output/gold/agreement_<set>_<labelers>.md. Free: reads local files only.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter

from common import LABELS, read_json
from rubric import load_rubric

GOLD = LABELS / "gold"
OUT = LABELS / "output" / "gold"
HUMAN = "human"  # blind hand labels (gold_labels_<set>.csv)
REVIEWED = "reviewed"  # hand review of two models' labels (gold_labels_<set>_reviewed.csv, labels/gold_page.py --review)
# Level renames between rubric versions, so earlier labels compare on today's levels. 5102cea87d4f was the wording
# of the practice round; it split today's `concrete` into `specific` and `partial`.
LEGACY = {"5102cea87d4f": {"failure_description": {"specific": "concrete", "partial": "concrete"}}}


def cohen_kappa(a: list[str], b: list[str]) -> float | None:
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    expected = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return None if expected == 1 else (observed - expected) / (1 - expected)


def slug(labeler: str) -> str:
    return labeler.replace("/", "_")


def load(labeler: str, gold_set: str, rubric: dict) -> dict:
    """{question_id: {"rank", "version", "labels", "reasons", "note"}} with levels mapped to the current rubric."""
    keys = [l["key"] for l in rubric["labels"]]
    if labeler in (HUMAN, REVIEWED):
        name = f"gold_labels_{gold_set}{'_reviewed' if labeler == REVIEWED else ''}.csv"
        with (GOLD / name).open(encoding="utf-8") as f:
            rows = {r["question_id"]: {"rank": int(r["gold_rank"]), "version": r["rubric_version"],
                                       "labels": {k: r[k] for k in keys}, "reasons": {}, "note": r["note"].strip()}
                    for r in csv.DictReader(f) if all(r[k] for k in keys)}
    else:
        rows = {qid: {"rank": d["gold_rank"], "version": d["rubric_version"], "labels": d["labels"],
                      "reasons": d.get("reasons", {}), "note": ""}
                for qid, d in read_json(OUT / f"{slug(labeler)}_{gold_set}.json").items()}
    for r in rows.values():
        for k, renames in LEGACY.get(r["version"], {}).items():
            r["labels"][k] = renames.get(r["labels"][k], r["labels"][k])
        for l in rubric["labels"]:
            if r["labels"][l["key"]] not in l["levels"]:
                raise SystemExit(f"{labeler}: {l['key']} = {r['labels'][l['key']]!r} is not a current level "
                                 f"(rubric {r['version']}); add a LEGACY mapping.")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--set", required=True, choices=["practice", "scoring"], dest="gold_set")
    parser.add_argument("--model", required=True, help="the labeler compared (a model id)")
    parser.add_argument("--against", default=HUMAN,
                        help="the other labeler: 'human' (blind, default), 'reviewed' (hand review) or a model id")
    args = parser.parse_args()
    rubric = load_rubric()
    a, b = load(args.against, args.gold_set, rubric), load(args.model, args.gold_set, rubric)
    versions = {r["version"] for r in a.values()} | {r["version"] for r in b.values()}
    ids = sorted(set(a) & set(b), key=lambda i: a[i]["rank"])
    name_a, name_b = ("Hand", "Model") if args.against == HUMAN else (args.against, args.model)

    lines = [f"# Agreement: {args.against} vs {args.model}, {args.gold_set} set", "",
             f"{len(ids)} questions labeled by both; rubric version(s) {', '.join(sorted(versions))} "
             f"(earlier levels mapped to the current ones).", "",
             f"| Label | Agree | Kappa | {name_a} levels | {name_b} levels |", "|---|---|---|---|---|"]
    disagreements = []
    for l in rubric["labels"]:
        k = l["key"]
        xa = [a[i]["labels"][k] for i in ids]
        xb = [b[i]["labels"][k] for i in ids]
        kappa = cohen_kappa(xa, xb)
        agree = sum(x == y for x, y in zip(xa, xb))
        fmt = lambda c: ", ".join(f"{lv} {c[lv]}" for lv in l["levels"] if c[lv])
        lines.append(f"| `{k}` | {agree}/{len(ids)} | {'n/a' if kappa is None else f'{kappa:.2f}'} | "
                     f"{fmt(Counter(xa))} | {fmt(Counter(xb))} |")
        disagreements += [(k, i, x, y) for i, x, y in zip(ids, xa, xb) if x != y]

    lines += ["", "## Disagreements", ""]
    if not disagreements:
        lines.append("None.")
    for k, i, x, y in disagreements:
        why = lambda r, who: f" {who}: {r['reasons'].get(k) or '(no reason)'}" if r["reasons"] else ""
        note = f" Hand note: {a[i]['note']}" if a[i]["note"] else ""
        lines.append(f"- `{k}`, question {a[i]['rank']} ({i}): {name_a.lower() if args.against == HUMAN else name_a} "
                     f"**{x}**, {name_b.lower() if args.against == HUMAN else name_b} **{y}**."
                     f"{why(a[i], name_a)}{why(b[i], name_b)}{note}")
    tag = slug(args.model) if args.against == HUMAN else f"{slug(args.against)}_vs_{slug(args.model)}"
    out = OUT / f"agreement_{args.gold_set}_{tag}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:len(rubric["labels"]) + 6]))
    print(f"\n{len(disagreements)} disagreements -> {out}")


if __name__ == "__main__":
    main()
