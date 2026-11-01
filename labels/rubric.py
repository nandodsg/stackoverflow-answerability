"""Reads labels/rubric.md, the single source of the quality-label definitions (specs/003, "Quality labels").

The label keys, their levels and each label's section of text are parsed from the file, so the hand-labeling page,
the labeling prompts and the agreement scoring all use the definitions exactly as written there. The version is a
hash of the file: every label row records it, which shows the scoring set was labeled on the frozen rubric.
"""

from __future__ import annotations

import hashlib
import re

from common import LABELS

RUBRIC = LABELS / "rubric.md"

HEADING = re.compile(r"^### \d+\. `(\w+)` — (.+)$")
LEVELS = re.compile(r"^Levels: (.+)$")
PROVENANCE = "## From the discovery candidates to this rubric"


def load_rubric() -> dict:
    text = RUBRIC.read_text(encoding="utf-8")
    labels, current = [], None
    for line in text.splitlines():
        if line.startswith("## ") or line.startswith("### "):
            current = None
            m = HEADING.match(line)
            if m:
                current = {"key": m.group(1), "title": m.group(2), "levels": [], "section": []}
                labels.append(current)
                continue
        if current is None:
            continue
        current["section"].append(line)
        m = LEVELS.match(line)
        if m and not current["levels"]:
            current["levels"] = re.findall(r"`(\w+)`", m.group(1))
    for label in labels:
        label["section"] = "\n".join(label["section"]).strip()
        label["reference"] = label["levels"][0]
        if len(label["levels"]) < 2:
            raise SystemExit(f"Rubric label {label['key']} has no 'Levels:' line with at least two levels.")
    if not labels:
        raise SystemExit("No labels found in labels/rubric.md.")
    # A labeler gets the definitions only: the closing section says which way each label leaned in the discovery
    # pass, and knowing that would pull a labeler toward guessing the outcome.
    judging_text = text.split(PROVENANCE)[0].rstrip() + "\n"
    if judging_text == text.rstrip() + "\n":
        raise SystemExit(f"labels/rubric.md has no '{PROVENANCE}' section to leave out of the labeling prompt.")
    return {
        "text": text,
        "judging_text": judging_text,
        "version": hashlib.sha256(text.encode("utf-8")).hexdigest()[:12],
        "labels": labels,
    }


if __name__ == "__main__":
    r = load_rubric()
    print(f"rubric version {r['version']}")
    for label in r["labels"]:
        print(f"  {label['key']}: {' / '.join(label['levels'])} (reference {label['reference']})")
