"""Labels gold-set questions with a language model on labels/rubric.md (specs/003, "Quality labels").

One call per question, so each judgment is independent, as the hand labeler's is. The model sees the same input as
the labeling page (original title, tags, year and Markdown body; no outcome) and returns one level per label, chosen
by a JSON schema built from the rubric's levels, plus a short reason per label (left out with --no-reasons).

Claude models are called on the Anthropic API; Google and xAI models (the two that write the reference labels the
hand labeler reviews) through the Vercel AI Gateway, with the same prompt, schema and effort.

  python labels/label_questions.py count --set practice                  # free: input tokens and cost estimate
  python labels/label_questions.py run --set practice --max-usd 2        # paid; skips questions already labeled
  python labels/label_questions.py run --set scoring --model google/gemini-4-argon --max-usd 4

`count` is exact for Claude models; for gateway models it counts with the Claude tokenizer as a proxy (free), so the
estimate is approximate. Output: labels/output/gold/<model>_<set>.csv (same columns as the hand labels, labeler = the
model; "/" in the model id becomes "_") and a .json with the reasons and token usage. Every call is logged in
labels/spend_log.csv. Compare with labels/agreement.py.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys

from common import GATEWAY_PRICES, LABELS, PRICES, anthropic_client, gateway_client, log_spend, read_json, write_json
from gold_page import load_questions
from rubric import load_rubric

EFFORT = "medium"
MAX_TOKENS = 16000  # per call, thinking included: the hard ceiling behind the worst-case cost
GATEWAY_MAX_TOKENS = 6000  # reasoning included; a call that hits it is logged and not saved
OUT = LABELS / "output" / "gold"
PROMPT = LABELS / "prompts" / "label_question.md"
FALLBACK = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}
COUNT_PROXY = "claude-opus-5-5"  # tokenizer used to estimate gateway models' input for free


def schema(rubric: dict, reasons: bool) -> dict:
    keys = [l["key"] for l in rubric["labels"]]
    props = {"labels": {
        "type": "object",
        "properties": {l["key"]: {"type": "string", "enum": l["levels"]} for l in rubric["labels"]},
        "required": keys,
        "additionalProperties": False,
    }}
    if reasons:
        props["reasons"] = {
            "type": "object",
            "properties": {k: {"type": "string"} for k in keys},
            "required": keys,
            "additionalProperties": False,
        }
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def render_question(q: dict) -> str:
    tags = ", ".join(q["original_tags"].split("|")) if q["original_tags"] else "(none)"
    return (f"Title: {q['original_title']}\nTags: {tags}\nYear: {q['creation_year']}\n\n"
            f"Body (Markdown):\n{q['original_body_text']}")


def system_prompt(rubric: dict) -> str:
    return PROMPT.read_text(encoding="utf-8").replace("{rubric}", rubric["judging_text"])


def request(q: dict, model: str, effort: str, rubric: dict, reasons: bool) -> dict:
    return {
        "model": model,
        "system": system_prompt(rubric),
        "messages": [{"role": "user", "content": render_question(q)}],
        "output_config": {"effort": effort, "format": {"type": "json_schema", "schema": schema(rubric, reasons)}},
    }


def gateway_request(q: dict, model: str, effort: str, rubric: dict, reasons: bool) -> dict:
    return {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt(rubric)},
                     {"role": "user", "content": render_question(q)}],
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "quality_labels", "strict": True, "schema": schema(rubric, reasons)}},
        "max_tokens": GATEWAY_MAX_TOKENS,
        "extra_body": {"reasoning": {"effort": effort}},
    }


def slug(model: str) -> str:
    return model.replace("/", "_")


def paths(model: str, gold_set: str):
    return OUT / f"{slug(model)}_{gold_set}.json", OUT / f"{slug(model)}_{gold_set}.csv"


def parse_result(text: str, rubric: dict, reasons: bool) -> dict:
    """The JSON the model returned, checked against the rubric: a level outside the rubric is an error, not a label."""
    text = text.strip()
    if text.startswith("```"):  # some providers wrap JSON in a fence even with a schema
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    result = json.loads(text)
    for l in rubric["labels"]:
        if result["labels"].get(l["key"]) not in l["levels"]:
            raise ValueError(f"{l['key']} = {result['labels'].get(l['key'])!r} is not a rubric level")
        if reasons and not isinstance(result.get("reasons", {}).get(l["key"]), str):
            raise ValueError(f"no reason for {l['key']}")
    return result


def count(questions: list[dict], model: str, effort: str, rubric: dict, reasons: bool) -> None:
    client = anthropic_client()
    gateway = model in GATEWAY_PRICES
    total = 0
    for q in questions:
        r = request(q, COUNT_PROXY if gateway else model, effort, rubric, reasons)
        total += client.messages.count_tokens(model=r["model"], system=r["system"], messages=r["messages"],
                                              output_config=r["output_config"]).input_tokens
    price = PRICES[model]
    n = len(questions)
    cap = GATEWAY_MAX_TOKENS if gateway else MAX_TOKENS
    # Output is unknown before the run: assume ~1,500 tokens per question (reasoning + labels + reasons).
    expected = (total * price["input"] + 1_500 * n * price["output"]) / 1e6
    ceiling = (total * price["input"] + cap * n * price["output"]) / 1e6
    proxy = f" (counted with the {COUNT_PROXY} tokenizer as a proxy)" if gateway else ""
    print(f"{model}, effort {effort}: {n} calls, {total:,} input tokens in all ({total // n:,} per call){proxy}")
    print(f"Expected cost ~US$ {expected:.2f}; ceiling US$ {ceiling:.2f} (every call at max_tokens={cap:,}).")


def call_anthropic(client, q, model, effort, rubric, reasons):
    with client.beta.messages.stream(max_tokens=MAX_TOKENS, **request(q, model, effort, rubric, reasons),
                                     **FALLBACK) as stream:
        msg = stream.get_final_message()
    served = msg.model if msg.model in PRICES else model
    text = next((b.text for b in msg.content if b.type == "text"), "")
    return served, msg.usage, msg.stop_reason == "end_turn", msg.stop_reason, text, msg.usage.to_dict()


def call_gateway(client, q, model, effort, rubric, reasons):
    resp = client.chat.completions.create(**gateway_request(q, model, effort, rubric, reasons))
    choice = resp.choices[0]
    return (resp.model or model, resp.usage, choice.finish_reason == "stop", choice.finish_reason,
            choice.message.content or "", resp.usage.model_dump())


def run(questions: list[dict], gold_set: str, model: str, effort: str, rubric: dict, reasons: bool,
        max_usd: float) -> None:
    gateway = model in GATEWAY_PRICES
    client, call = (gateway_client(), call_gateway) if gateway else (anthropic_client(), call_anthropic)
    json_path, csv_path = paths(model, gold_set)
    done = read_json(json_path) if json_path.exists() else {}
    if done and next(iter(done.values()))["rubric_version"] != rubric["version"]:
        sys.exit(f"{json_path.name} was labeled on another rubric version; move it aside before re-labeling.")
    run_name = f"gold-{gold_set}-{slug(model)}-{rubric['version']}"
    spent = 0.0
    for q in questions:
        qid = str(q["question_id"])
        if qid in done:
            continue
        if spent >= max_usd:
            print(f"Stopped: US$ {spent:.2f} spent, cap US$ {max_usd:.2f}.")
            break
        served, usage, finished, stop, text, usage_dict = call(client, q, model, effort, rubric, reasons)
        # Price by the model asked for: a gateway model id comes back as served, Claude may fall back to another.
        cost = log_spend(run_name, f"q{q['gold_rank']:03d}", served if served in PRICES else model, usage)
        spent += cost
        print(f"  {gold_set} {q['gold_rank']:3d} ({qid}): {usage_dict.get('input_tokens', usage_dict.get('prompt_tokens'))} in, "
              f"{usage_dict.get('output_tokens', usage_dict.get('completion_tokens'))} out, US$ {cost:.3f}, stop {stop}")
        if not finished:
            print(f"    not saved: stopped with {stop}")
            continue
        try:
            result = parse_result(text, rubric, reasons)
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            print(f"    not saved: {e}")
            continue
        done[qid] = {"gold_rank": q["gold_rank"], "rubric_version": rubric["version"], "served_by": served,
                     "effort": effort, "usd": round(cost, 4), "usage": usage_dict, **result}
        write_json(json_path, done)  # after every call, so an interrupted run resumes where it stopped
    write_csv(done, gold_set, model, rubric, csv_path)
    print(f"US$ {spent:.2f} this run; {len(done)} of {len(questions)} labeled -> {csv_path}")


def write_csv(done: dict, gold_set: str, model: str, rubric: dict, path) -> None:
    keys = [l["key"] for l in rubric["labels"]]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["question_id", "gold_set", "gold_rank", "labeler", "rubric_version", *keys, "note",
                    "labeled_at_utc"])
        for qid, d in sorted(done.items(), key=lambda kv: kv[1]["gold_rank"]):
            w.writerow([qid, gold_set, d["gold_rank"], model, d["rubric_version"], *[d["labels"][k] for k in keys],
                        "", ""])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=["count", "run"])
    parser.add_argument("--set", required=True, choices=["practice", "scoring"], dest="gold_set")
    parser.add_argument("--model", default="claude-opus-5-5", choices=sorted(PRICES))
    parser.add_argument("--effort", default=EFFORT, choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--no-reasons", action="store_true", help="labels only (cheaper output)")
    parser.add_argument("--max-usd", type=float, help="run only: stop starting new calls once this much is spent")
    args = parser.parse_args()
    rubric = load_rubric()
    questions = [q for q in load_questions() if q["gold_set"] == args.gold_set]
    if args.mode == "count":
        count(questions, args.model, args.effort, rubric, not args.no_reasons)
    else:
        if args.max_usd is None:
            sys.exit("run needs --max-usd (the spending cap you approved).")
        OUT.mkdir(parents=True, exist_ok=True)
        run(questions, args.gold_set, args.model, args.effort, rubric, not args.no_reasons, args.max_usd)


if __name__ == "__main__":
    main()
