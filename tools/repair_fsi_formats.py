#!/usr/bin/env python3
"""
Generate an optional FSI drill-format patch for experiments.

Why:
- Volume 2 OCR sometimes corrupts `model_sentence` / `cues` in `data/drills.json`.
- The web app repairs these in-memory using `data/exercice_structure.json`.
- This script lets you materialize a small override file for faster iteration:
  `data/fsi_drill_format_patch.json` (drill_id -> {model_sentence, cues, meta})

Usage:
  python3 tools/repair_fsi_formats.py
  python3 tools/repair_fsi_formats.py --out data/fsi_drill_format_patch.json
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


LEGACY_RE = re.compile(r"^fsi_[^_]+_([A-Z])-(\d+)_0*(\d+)$")


def normalize_text(text: str) -> str:
    return " ".join(text.replace("’", "'").split()).strip().lower()


def has_letters(text: str) -> bool:
    return bool(re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]", text or ""))


def tokenize(text: str) -> List[str]:
    if not text:
        return []
    return re.findall(r"[\wÀ-ÖØ-öø-ÿ]+(?:['’][\wÀ-ÖØ-öø-ÿ]+)*|[.,!?;:()]", text, flags=re.UNICODE)


def join_tokens(tokens: List[str]) -> str:
    if not tokens:
        return ""
    s = " ".join(tokens)
    s = re.sub(r"\s+([.,!?;:()])", r"\1", s)
    return s.strip()


def extract_cue(model_sentence: str, response_sentence: str) -> str:
    model_norm = normalize_text(model_sentence)
    response_norm = normalize_text(response_sentence)

    model_tokens_norm = tokenize(model_norm)
    response_tokens_norm = tokenize(response_norm)
    response_tokens_orig = tokenize(response_sentence)

    if not model_tokens_norm or not response_tokens_norm or not response_tokens_orig:
        return ""
    if len(response_tokens_norm) != len(response_tokens_orig):
        return ""

    start = 0
    while start < len(model_tokens_norm) and start < len(response_tokens_norm) and model_tokens_norm[start] == response_tokens_norm[start]:
        start += 1

    end = 0
    while (
        end < (len(model_tokens_norm) - start)
        and end < (len(response_tokens_norm) - start)
        and model_tokens_norm[len(model_tokens_norm) - 1 - end] == response_tokens_norm[len(response_tokens_norm) - 1 - end]
    ):
        end += 1

    cue = join_tokens(response_tokens_orig[start : len(response_tokens_orig) - end])
    cue_norm = normalize_text(cue)
    if not cue_norm:
        return ""
    if cue_norm in (normalize_text(model_sentence), normalize_text(response_sentence)):
        return ""
    if len(cue) > 120:
        return ""
    return cue


@dataclass(frozen=True)
class Candidate:
    model_sentence: str
    response: str
    response_norm: str


def parse_legacy_id(legacy_id: str) -> Optional[Tuple[str, int]]:
    m = LEGACY_RE.match(legacy_id or "")
    if not m:
        return None
    exercice_id = f"{m.group(1)}{int(m.group(2))}"
    drill_number = int(m.group(3))
    return exercice_id, drill_number


def build_indices(exercice_structure: Dict[str, Any]) -> Tuple[Dict[str, List[Candidate]], Dict[str, List[Candidate]]]:
    by_key: Dict[str, List[Candidate]] = {}
    by_ex: Dict[str, List[Candidate]] = {}

    for ex in exercice_structure.get("exercices", []):
        unit = ex.get("unit")
        exercice_id = ex.get("exercice_id")
        drills = ex.get("drills")
        if not isinstance(unit, int) or not isinstance(exercice_id, str) or not isinstance(drills, list) or not drills:
            continue

        canonical = next((d for d in drills if d.get("is_canonical") and isinstance(d.get("french"), str) and d["french"].strip()), None)
        canonical = canonical or next((d for d in drills if isinstance(d.get("french"), str) and d["french"].strip()), None)
        model_sentence = (canonical or {}).get("french", "").strip()
        if not has_letters(model_sentence):
            continue

        for d in drills:
            number = d.get("number")
            response = d.get("french", "")
            if not isinstance(number, int) or not isinstance(response, str):
                continue
            response = response.strip()
            if not response:
                continue
            cand = Candidate(model_sentence=model_sentence, response=response, response_norm=normalize_text(response))

            key = f"{unit}|{exercice_id}|{number}"
            by_key.setdefault(key, []).append(cand)
            ex_key = f"{unit}|{exercice_id}"
            by_ex.setdefault(ex_key, []).append(cand)

    return by_key, by_ex


def pick_best(candidates: List[Candidate], response_sentence: str) -> Tuple[Candidate, str]:
    response_norm = normalize_text(response_sentence)
    exact = next((c for c in candidates if c.response_norm == response_norm), None)
    if exact:
        return exact, "exact"

    resp_tokens = set(tokenize(response_norm))
    best = candidates[0]
    best_score = -1.0
    for c in candidates:
        cand_tokens = set(tokenize(c.response_norm))
        if not cand_tokens or not resp_tokens:
            continue
        inter = len(cand_tokens.intersection(resp_tokens))
        score = inter / max(1, max(len(cand_tokens), len(resp_tokens)))
        if score > best_score:
            best_score = score
            best = c
    return best, "overlap"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--drills", default="data/drills.json")
    parser.add_argument("--exercice-structure", default="data/exercice_structure.json")
    parser.add_argument("--out", default="data/fsi_drill_format_patch.json")
    args = parser.parse_args()

    drills_path = Path(args.drills)
    ex_path = Path(args.exercice_structure)
    out_path = Path(args.out)

    drills_db = json.loads(drills_path.read_text(encoding="utf-8"))
    ex_struct = json.loads(ex_path.read_text(encoding="utf-8"))

    by_key, by_ex = build_indices(ex_struct)

    patch: Dict[str, Any] = {}
    total = 0
    repaired = 0
    used_fallback = 0

    for d in drills_db.get("drills", []):
        t = d.get("type")
        unit = d.get("unit")
        if not (isinstance(t, str) and t.startswith("fsi_") and isinstance(unit, int) and unit >= 13):
            continue

        legacy_id = d.get("legacy_id")
        if not isinstance(legacy_id, str):
            continue
        parsed = parse_legacy_id(legacy_id)
        if not parsed:
            continue
        exercice_id, drill_number = parsed

        response_sentence = ""
        er = d.get("expected_responses")
        if isinstance(er, list) and er and isinstance(er[0], str):
            response_sentence = er[0].strip()
        response_sentence = response_sentence or (d.get("french_formal") or "").strip()
        if not has_letters(response_sentence):
            continue

        total += 1
        key = f"{unit}|{exercice_id}|{drill_number}"
        candidates = by_key.get(key)
        source = "byKey"
        if not candidates:
            candidates = by_ex.get(f"{unit}|{exercice_id}")
            source = "byExercise"
        if not candidates:
            continue

        cand, match = pick_best(candidates, response_sentence)
        model_sentence = cand.model_sentence.strip()
        if not has_letters(model_sentence):
            continue

        cue = extract_cue(model_sentence, response_sentence)
        patch[d["id"]] = {
            "model_sentence": model_sentence,
            "cues": [cue] if cue else [],
            "meta": {
                "unit": unit,
                "exercice_id": exercice_id,
                "drill_number": drill_number,
                "source": source,
                "match": match,
                "legacy_id": legacy_id,
            },
        }
        repaired += 1
        if source == "byExercise":
            used_fallback += 1

    out_payload = {
        "generated_by": "tools/repair_fsi_formats.py",
        "drills_total_considered": total,
        "drills_patched": repaired,
        "patched_via_exercise_fallback": used_fallback,
        "patch": patch,
    }

    out_path.write_text(json.dumps(out_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {repaired} drill patches to {out_path}")
    print(f"Total considered: {total}, fallback used: {used_fallback}")


if __name__ == "__main__":
    main()

