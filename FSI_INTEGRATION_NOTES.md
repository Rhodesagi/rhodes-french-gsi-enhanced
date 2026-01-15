## What’s different from `rhodes-french` (baseline)

The baseline Rhodes French course (`rhodes-french`) is primarily “sentence drills” with audio mapping and SRS.

This repo (`rhodes-french-gsi-enhanced`) adds **FSI drill formats**, which are structurally different:
- **Model sentence**: the base pattern the learner starts from.
- **Cue**: the substitution/transform item that changes the pattern.
- **Expected response**: what the learner must produce.

In the app, these show up as:
- Prompt = `model_sentence` (or cue fallback), plus
- Hints = `Cues:` + `Produce:` (expected response).

## The core integration problem (why prior attempts “failed”)

FSI Volume 2 extraction is OCR’d and includes noisy “layout junk” that can leak into the data as fake model sentences/cues (e.g. `h.`).

If the app uses a corrupted `model_sentence`, the prompt becomes meaningless even if `expected_responses` is correct.

## Current approach in this repo (flexible + hackable)

1. **Primary repair path (default)**: At load time, use `data/exercice_structure.json` (exercise grouping + canonical model sentence) and each drill’s `legacy_id` to repair:
   - `model_sentence`
   - `cues` (computed via diff between model and expected response)

2. **Optional override patch (experimental)**:
   - Generate `data/fsi_drill_format_patch.json` via `tools/repair_fsi_formats.py`.
   - Launch with `?fsiPatch=1` to apply it on top of the default repair.

3. **Debugging**:
   - Launch with `?debugFsi=1` to show which repair path was used in the hint box.

## Response-drill “blank slot” cues (Volume 1 PDFs)

In the original FSI PDFs, many Response Drill prompts intentionally include a blank slot (often printed as dots / bullets) like `Demandez à .•• ...`.
In this web app we keep the placeholder (`...`) but also fill it at runtime with a safe stand-in (e.g. `ce monsieur` / `cette dame`) so self-study prompts and expected responses are “typeable”.

## Deep-linking (debugging)

- Open a specific drill directly: `?card=<drill_id>`
- Keep the URL synced to the current drill as you advance: `&trackCard=1`

## Audiolingual sequencing (grouped → interleaved)

The goal is to preserve the “blocked practice” feel early (many similar prompts in a row), then gradually interleave.

- Default sequencing mode: `audiolingual`
- Switch modes: `?seq=audiolingual` or `?seq=mixed`
- Tuning knobs:
  - `?groupStart=<n>`: initial block size within a format/model group
  - `?groupEnd=<n>`: final block size toward the end of the session
  - `?spaced=0`: disable the extra in-session spaced repeats
- In-session “repeat” items are marked as `(repeat)` in the progress label and do **not** affect SRS scheduling/progress.
