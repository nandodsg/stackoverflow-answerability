"""Discovery pass of the P3 quality labels (specs/003, "Quality labels").

Reads the ~200 contrastive pairs of int_label_discovery_pairs (same tag, year and has-code-block value; one question
with an accepted answer, one unanswered), then asks a large model in two stages:

  blind   batches of 20 pairs, outcome hidden and A/B order shuffled: the model guesses which question got the
          accepted answer and lists the differences it sees (prompts/discovery_blind.md)
  reveal  one call with every note, the true outcomes and the measured guess accuracy: the model proposes candidate
          labels grounded in the differences that actually separated the two outcomes (prompts/discovery_reveal.md)

Hiding the outcome keeps the model from rationalizing noise into reasons, and the guess accuracy measures how far
text alone separates the outcomes. Outputs go to labels/output/discovery/; the curated rubric is made by hand from
candidate_labels.md.

  python labels/discover_labels.py count             # free: exact input tokens (token-count endpoint) and cost estimate
  python labels/discover_labels.py run --max-usd 8   # paid: blind batches, then the reveal; skips finished batches

Question text is read once from int_post_history_scan (the stored 5% sample) and cached in labels/.cache/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys

from common import (BQ_DATASET, BQ_PROJECT, CACHE, LABELS, PRICES, anthropic_client, bq_query, log_spend,
                    read_json, write_json)

MODEL = "claude-opus-5-5"
EFFORT = "high"
BATCH_SIZE = 20
MAX_TOKENS = 32000  # per call, thinking included: the hard ceiling behind the worst-case cost
RUN = "discovery-2026-10-31"
OUT = LABELS / "output" / "discovery"
PROMPTS = LABELS / "prompts"
TEXT_CACHE = CACHE / "discovery_pairs.json"
FALLBACK = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}

BLIND_SCHEMA = {
    "type": "object",
    "properties": {
        "pairs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "pair_id": {"type": "string"},
                    "guess": {"type": "string", "enum": ["A", "B"]},
                    "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                    "differences": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "quality": {"type": "string"},
                                "kind": {"type": "string", "enum": ["writing", "topic", "measured"]},
                                "a": {"type": "string"},
                                "b": {"type": "string"},
                                "favors": {"type": "string", "enum": ["A", "B", "neither"]},
                            },
                            "required": ["quality", "kind", "a", "b", "favors"],
                            "additionalProperties": False,
                        },
                    },
                    "deciding_reason": {"type": "string"},
                },
                "required": ["pair_id", "guess", "confidence", "differences", "deciding_reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["pairs"],
    "additionalProperties": False,
}

REVEAL_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_labels": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "definition": {"type": "string"},
                    "levels": {"type": "array", "items": {"type": "string"}},
                    "decision_rule": {"type": "string"},
                    "borderline_case": {"type": "string"},
                    "pairs_showing_difference": {"type": "integer"},
                    "pairs_favoring_accepted": {"type": "integer"},
                    "example_pair_ids": {"type": "array", "items": {"type": "string"}},
                    "rule_based_neighbour": {"type": "string"},
                    "concerns": {"type": "string"},
                },
                "required": ["name", "definition", "levels", "decision_rule", "borderline_case",
                             "pairs_showing_difference", "pairs_favoring_accepted", "example_pair_ids",
                             "rule_based_neighbour", "concerns"],
                "additionalProperties": False,
            },
        },
        "rejected_ideas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "reason": {"type": "string"}},
                "required": ["name", "reason"],
                "additionalProperties": False,
            },
        },
        "summary": {"type": "string"},
    },
    "required": ["candidate_labels", "rejected_ideas", "summary"],
    "additionalProperties": False,
}


def load_pairs() -> list[dict]:
    """The pairs with both questions' original title and body; read from BigQuery once, then from the cache."""
    if TEXT_CACHE.exists():
        return read_json(TEXT_CACHE)
    sql = f"""
        with p as (select * from `{BQ_PROJECT}.{BQ_DATASET}.int_label_discovery_pairs`)
        select
            p.pair_id, p.creation_year, p.primary_tag, p.has_code_block,
            p.accepted_question_id, acc.original_title as accepted_title, acc.original_body_text as accepted_body,
            p.unanswered_question_id, una.original_title as unanswered_title, una.original_body_text as unanswered_body
        from p
        join `{BQ_PROJECT}.{BQ_DATASET}.int_post_history_scan` as acc
            on acc.post_id = p.accepted_question_id and acc.post_kind = 'question'
            and acc.creation_year between 2018 and 2021
        join `{BQ_PROJECT}.{BQ_DATASET}.int_post_history_scan` as una
            on una.post_id = p.unanswered_question_id and una.post_kind = 'question'
            and una.creation_year between 2018 and 2021
        order by p.pair_id
    """
    pairs = bq_query(sql)
    if len(pairs) != 200:
        sys.exit(f"Expected 200 pairs, got {len(pairs)}.")
    write_json(TEXT_CACHE, pairs)
    return pairs


def accepted_is_a(pair_id: str) -> bool:
    """Fixed pseudo-random A/B order, so the accepted question is not always in the same position."""
    return hashlib.sha256(f"{RUN}:{pair_id}".encode()).digest()[0] % 2 == 0


def render_pair(p: dict) -> str:
    acc = (p["accepted_title"], p["accepted_body"])
    una = (p["unanswered_title"], p["unanswered_body"])
    a, b = (acc, una) if accepted_is_a(p["pair_id"]) else (una, acc)
    code = "both have a code block" if p["has_code_block"] else "neither has a code block"
    parts = [f'<pair id="{p["pair_id"]}" tag="{p["primary_tag"]}" year="{p["creation_year"]}" code="{code}">']
    for label, (title, body) in (("A", a), ("B", b)):
        parts.append(f'<question label="{label}">\nTitle: {title}\n\nBody (Markdown):\n{body}\n</question>')
    parts.append("</pair>")
    return "\n".join(parts)


def blind_request(batch: list[dict]) -> dict:
    content = (f"Here are {len(batch)} pairs. Return one entry per pair, in the order given.\n\n"
               + "\n\n".join(render_pair(p) for p in batch))
    return {
        "model": MODEL,
        "system": (PROMPTS / "discovery_blind.md").read_text(encoding="utf-8"),
        "messages": [{"role": "user", "content": content}],
        "output_config": {"effort": EFFORT, "format": {"type": "json_schema", "schema": BLIND_SCHEMA}},
    }


def reveal_request(pairs: list[dict], notes: dict[str, dict]) -> dict:
    rows, correct, by_conf = [], 0, {}
    for p in pairs:
        n = notes[p["pair_id"]]
        truth = "A" if accepted_is_a(p["pair_id"]) else "B"
        hit = n["guess"] == truth
        correct += hit
        c = by_conf.setdefault(n["confidence"], [0, 0])
        c[0] += hit
        c[1] += 1
        rows.append({
            "pair_id": p["pair_id"], "tag": p["primary_tag"], "year": p["creation_year"],
            "code": bool(p["has_code_block"]), "accepted": truth, "guess": n["guess"],
            "confidence": n["confidence"], "guess_right": hit,
            "deciding_reason": n["deciding_reason"], "differences": n["differences"],
        })
    accuracy = {
        "overall": f"{correct} of {len(pairs)} right ({correct / len(pairs):.0%})",
        "by_confidence": {k: f"{v[0]} of {v[1]} right ({v[0] / v[1]:.0%})" for k, v in sorted(by_conf.items())},
    }
    content = ("Guess accuracy, computed by the analyst:\n" + json.dumps(accuracy, indent=1)
               + "\n\nNotes per pair (one JSON object per line):\n"
               + "\n".join(json.dumps(r, ensure_ascii=False) for r in rows))
    return {
        "model": MODEL,
        "system": (PROMPTS / "discovery_reveal.md").read_text(encoding="utf-8"),
        "messages": [{"role": "user", "content": content}],
        "output_config": {"effort": EFFORT, "format": {"type": "json_schema", "schema": REVEAL_SCHEMA}},
    }, accuracy


def call(client, request: dict, step: str) -> dict:
    with client.beta.messages.stream(max_tokens=MAX_TOKENS, **request, **FALLBACK) as stream:
        msg = stream.get_final_message()
    served = msg.model if msg.model in PRICES else MODEL
    cost = log_spend(RUN, step, served, msg.usage)
    print(f"  {step}: {msg.usage.input_tokens} in, {msg.usage.output_tokens} out, US$ {cost:.2f}, "
          f"served by {msg.model}, stop {msg.stop_reason}")
    if msg.stop_reason != "end_turn":
        sys.exit(f"{step} stopped with {msg.stop_reason}; nothing saved for it.")
    text = next(b.text for b in msg.content if b.type == "text")
    return {"model": msg.model, "usage": msg.usage.to_dict(), "usd": round(cost, 4), "result": json.loads(text)}


def batches(pairs: list[dict]) -> list[list[dict]]:
    return [pairs[i:i + BATCH_SIZE] for i in range(0, len(pairs), BATCH_SIZE)]


def count(pairs: list[dict]) -> None:
    client = anthropic_client()
    price = PRICES[MODEL]
    total_in = 0
    for i, batch in enumerate(batches(pairs), 1):
        r = blind_request(batch)
        n = client.messages.count_tokens(model=r["model"], system=r["system"], messages=r["messages"],
                                         output_config=r["output_config"]).input_tokens
        total_in += n
        print(f"  blind batch {i:02d}: {n:,} input tokens")
    k = len(batches(pairs))
    # Output is unknown before the run: assume ~15k tokens per blind batch (notes + thinking) and a reveal call that
    # reads ~250 tokens of notes per pair and writes ~15k. The ceiling uses MAX_TOKENS on every call.
    reveal_in = 250 * len(pairs) + 2_000
    expected = ((total_in + reveal_in) * price["input"] + (15_000 * k + 15_000) * price["output"]) / 1e6
    ceiling = ((total_in + reveal_in) * price["input"] + MAX_TOKENS * (k + 1) * price["output"]) / 1e6
    print(f"\n{MODEL}, effort {EFFORT}: blind input {total_in:,} tokens over {k} calls, reveal input ~{reveal_in:,}")
    print(f"Expected cost ~US$ {expected:.2f}; ceiling US$ {ceiling:.2f} (every call at max_tokens={MAX_TOKENS:,}).")


def run(pairs: list[dict], max_usd: float) -> None:
    client = anthropic_client()
    spent = 0.0
    notes: dict[str, dict] = {}
    for i, batch in enumerate(batches(pairs), 1):
        path = OUT / f"blind_batch_{i:02d}.json"
        if not path.exists():
            if spent >= max_usd:
                sys.exit(f"Stopped: US$ {spent:.2f} spent, cap US$ {max_usd:.2f}.")
            out = call(client, blind_request(batch), f"blind_batch_{i:02d}")
            ids = [p["pair_id"] for p in batch]
            got = [n["pair_id"] for n in out["result"]["pairs"]]
            if got != ids:
                sys.exit(f"Batch {i:02d}: pair ids came back as {got}, expected {ids}; not saved.")
            write_json(path, out)
            spent += out["usd"]
        for n in read_json(path)["result"]["pairs"]:
            notes[n["pair_id"]] = n
    if spent >= max_usd:
        sys.exit(f"Stopped before the reveal: US$ {spent:.2f} spent, cap US$ {max_usd:.2f}.")
    request, accuracy = reveal_request(pairs, notes)
    print(f"Guess accuracy: {accuracy}")
    out = call(client, request, "reveal")
    out["guess_accuracy"] = accuracy
    write_json(OUT / "reveal.json", out)
    write_candidates_md(out)


def write_candidates_md(out: dict) -> None:
    r = out["result"]
    lines = ["# Candidate quality labels (discovery pass, not yet curated)", "",
             f"Model {out['model']}; guess accuracy {out['guess_accuracy']['overall']}, by confidence "
             f"{out['guess_accuracy']['by_confidence']}.", "", "## Summary", "", r["summary"], "",
             "## Candidates", ""]
    for i, c in enumerate(r["candidate_labels"], 1):
        lines += [f"### {i}. {c['name']}", "", c["definition"], "",
                  f"- Levels: {' / '.join(c['levels'])}",
                  f"- Decision rule: {c['decision_rule']}",
                  f"- Borderline case: {c['borderline_case']}",
                  f"- Support: {c['pairs_showing_difference']} pairs showed it, "
                  f"{c['pairs_favoring_accepted']} favoring the accepted question",
                  f"- Example pairs: {', '.join(c['example_pair_ids'])}",
                  f"- Rule-based neighbour: {c['rule_based_neighbour']}",
                  f"- Concerns: {c['concerns']}", ""]
    lines += ["## Rejected ideas", ""] + [f"- **{x['name']}**: {x['reason']}" for x in r["rejected_ideas"]]
    (OUT / "candidate_labels.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=["count", "run"])
    parser.add_argument("--max-usd", type=float, help="run only: stop starting new calls once this much is spent")
    args = parser.parse_args()
    pairs = load_pairs()
    if args.mode == "count":
        count(pairs)
    else:
        if args.max_usd is None:
            sys.exit("run needs --max-usd (the spending cap you approved).")
        run(pairs, args.max_usd)


if __name__ == "__main__":
    main()
