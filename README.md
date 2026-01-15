# Rhodes French - FSI Enhanced Edition

A complete, free French language course with **11,330 drill exercises** (7,799 original Rhodes drills + 3,531 FSI French Basic Course drills) and native speaker audio.

## Try It Now

Visit: **https://rhodesagi.github.io/rhodes-french-gsi-enhanced/**

## Features

- **11,330 total drills** (7,799 original Rhodes drills + 3,531 FSI French Basic Course drills)
- **FSI Units 13-23** integrated with precise audio mapping
- **Native French audio recordings** for all original drills + mapped FSI drills
- **47% of FSI drills** have exact audio matches (1,658 drills), remainder use high-quality TTS
- **Grammar hints and error analysis**
- **Progress tracking** (saved locally)
- **Works offline** after first load
- **FSI drill types**: substitution, transformation, variation, response, review, lexical, question
- **Debuggable drills**: deep-link to a specific card with `?card=<drill_id>` (optionally `&trackCard=1` to keep the URL updated as you advance)
- **Audiolingual sequencing**: grouped practice early → gradual interleaving (`?seq=audiolingual` / `?seq=mixed`, plus `?groupStart=` / `?groupEnd=` / `?spaced=0`)

## FSI Integration Details

This enhanced edition integrates the complete **FSI French Basic Course Volumes 1 & 2** (Units 13-23) with precise sentence-to-sentence audio mapping. The integration includes:

- **3,531 FSI drills** across 7 exercise types
- **Precise audio mapping** using exact model sentence matching (not approximate frequency)
- **Grouped mapping** ensures drills sharing model sentences use the same audio
- **Audio validation** - all mapped audio files verified to exist
- **TTS fallback** - unmapped FSI drills use browser text-to-speech with French accent

### Audio Mapping Statistics
- **Total FSI drills**: 3,531
- **Drills with audio mapping**: 1,658 (47%)
- **Drills using TTS fallback**: 1,873 (53%)
- **Mapping method**: Exact model sentence grouping (1,658 unique model sentences)

### Technical Implementation
- **Detection**: FSI drills identified by `drill.type.startsWith('fsi_')`
- **CSS class**: `fsi-drill` for visual differentiation
- **Audio loading**: Combined `reverse_audio_mapping.json` + `fsi_audio_mapping.json`
- **Drill formats**: `exercice_structure.json` + `legacy_id` repair `model_sentence`/`cues` at load time (fixes OCR-noise like stray `h.` tokens)
- **Optional patch file**: Generate `data/fsi_drill_format_patch.json` with `python3 tools/repair_fsi_formats.py` and load with `?fsiPatch=1` for experiments
- **Debug**: Add `?debugFsi=1` to show which repair path was used for an FSI drill
- **Auto-direction**: FSI drills automatically switch away from FR→EN (FSI drills rarely have reliable English prompts)
- **Audiolingual repeats**: extra “repeat” instances inserted for practice do not affect SRS scheduling/progress
- **Cache versioning**: Automatic cache busting on updates

## Repository Structure

This repository is a fork of the original [Rhodes French](https://github.com/Rhodesagi/rhodes-french) with FSI integration. The main branch contains the complete enhanced web app ready for GitHub Pages deployment.

---

*By Rhodes AI* | *FSI Integration by AHGI Alliance*
