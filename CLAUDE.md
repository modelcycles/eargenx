# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EarGenX is a single-file Python CLI tool that generates randomized ear training (청음) exam questions for music education. It supports two question categories (single notes and intervals), multiple output formats, and configurable difficulty levels.

## Running the Tool

```bash
# Activate virtual environment first (recommended)
source .venv/Scripts/activate   # Windows/MINGW64
# or
.venv/Scripts/python eargenx.py ...

# Basic usage
python eargenx.py                                           # Random step, 10 questions, print
python eargenx.py -r CAT_SN_SC01 -a 20                    # 20 questions from a course
python eargenx.py -r CAT_INT -r CAT_SN -a 10 -f xlsx csv  # Multiple ranges/formats
python eargenx.py -r CAT_SN_SC01_P03_S04 -a 5 --seed 42   # Reproducible output
python eargenx.py -r CAT_INT_SC01_P01 --difficulty stairs  # Staircase difficulty curve
```

## CLI Arguments

| Flag | Description |
|------|-------------|
| `-r, --range` | Hierarchical range ID (repeatable): category → course → part → step |
| `-a, --amount` | Questions per range (default: 10) |
| `-d, --difficulty` | `1`/`2`/`3` (fixed) or `linear`/`stairs`/`fixed` (curve) |
| `-s, --shuffle` | Randomize final question order |
| `-f, --format` | `print` / `csv` / `xlsx` / `md` (multiple allowed) |
| `-o, --output` | Output directory (default: `example/`) |
| `--seed` | Integer seed for reproducible generation |

## Dependencies

```bash
pip install -r requirements.txt   # pandas, openpyxl
```

The tool degrades gracefully when `pandas`/`openpyxl` are missing — CSV/XLSX output will be unavailable but `print` and `md` still work.

## Architecture

The entire application lives in a single file (`eargenx.py`, ~1,100 lines) organized into 13 numbered sections:

1. **System constants** — MIDI range (C3=48 to C6=84)
2. **Curriculum data** — Static hierarchical data: categories → courses → parts → steps (60+ steps)
3. **Lookup tables** — `STEP_LOOKUP`, `CATEGORY_LOOKUP` for O(1) access
4. **Music utilities** — MIDI ↔ note name conversion, interval semitone math, enharmonic normalization, note pool parsing
5. **Answer type rules** — `ANSWER_TYPE_RULES` matrix: 10 question types (same/different, multiple choice, subjective, etc.)
6. **Difficulty rules** — `DIFFICULTY_RULES` for 3 levels: octave ranges and distractor proximity strategies
7. **`SingleNoteGenerator`** — Generates single-note questions; session history prevents repetition; builds distractors by proximity
8. **`IntervalGenerator`** — Generates interval questions (ascending/descending/harmonic); difficulty adjusts root note ranges
9. **Batch generation** — `generate_batch()` and `difficulty_curve()` orchestrate question sets
10. **Range resolution** — `resolve_range()` maps a hierarchical ID string to a list of step IDs
11. **Output formatters** — `output_print()`, `output_csv()`, `output_xlsx()`, `output_md()`
12. **CLI** — `build_parser()` via `argparse`
13. **`main()`** — Top-level orchestration: parse args → resolve ranges → generate → shuffle → output

## Curriculum Hierarchy

```
Category (CAT_SN / CAT_INT)
└── Course  (e.g. CAT_SN_SC01, CAT_INT_SC02)
    └── Part   (e.g. CAT_SN_SC01_P01)
        └── Step   (e.g. CAT_SN_SC01_P01_S01)
```

- **CAT_SN** — Single note discrimination (7-tone pentatonic SC01, 12-tone chromatic SC02)
- **CAT_INT** — Interval identification (SC01–SC06 covering progressively wider interval sets)

Each step definition includes: question type, note/interval pool, answer type key, and difficulty.

## Key Design Patterns

- **Session-aware generation**: Both generators track history within a batch to avoid immediate repetition.
- **Distractor strategy**: Difficulty level controls whether wrong answers are far (≥5 semitones, easy) or close (≤2 semitones, hard).
- **Data-driven curriculum**: All learning content is encoded in `CURRICULUM_DATA` tuples; adding a new step only requires appending a row there and updating `STEP_LOOKUP`.
- **Optional dependencies**: `HAS_PANDAS` / `HAS_OPENPYXL` flags gate format-specific code paths.

## Git Commit Convention

- **Title**: Always in English
- **Body**: Bilingual — Korean description first, then English description

Example:
```
fix: correct height_compare answer/choices bug

- _build_height_compare()에서 항상 '같음'만 반환하던 로직 수정
- Fixed _build_height_compare() to return either '같음' or '다름'
```
