#!/usr/bin/env python3
"""
eargenx.py — 청음 문제 더미데이터 생성기

사용법:
  python eargenx.py                                              # 기본값 (랜덤 스텝, 10문제, print)
  python eargenx.py --range CAT_SN_SC01 --amount 20            # 단일음 SC01에서 20문제
  python eargenx.py -r CAT_SN -r CAT_INT -a 10 -f xlsx csv    # 두 카테고리, 각 10문제, xlsx+csv
  python eargenx.py -r CAT_INT_SC01_P01 --difficulty stairs    # 계단식 난이도

범위 형식 (가장 상위 카테고리부터 시작해야 함):
  CAT_SN                        → 단일음 전체
  CAT_SN_SC01                   → 단일음 7음계 코스 전체
  CAT_SN_SC01_P01               → 파트 전체
  CAT_SN_SC01_P01_S01           → 특정 스텝
  CAT_INT                       → 음정 전체
"""

import argparse
import math
import os
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── 선택적 패키지 ────────────────────────────────────────────────────────────
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import openpyxl  # noqa: F401
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


# ══════════════════════════════════════════════════════════════════════════════
# 1. 시스템 상수
# ══════════════════════════════════════════════════════════════════════════════
MIDI_MIN = 48   # C3
MIDI_MAX = 84   # C6


# ══════════════════════════════════════════════════════════════════════════════
# 2. 커리큘럼 데이터 (ear_training_v4.ipynb 기반)
# ══════════════════════════════════════════════════════════════════════════════
CATEGORY_DATA = [
    ('CAT_SN',  '단일음'),
    ('CAT_INT', '음정'),
]

COURSE_DATA = [
    # category_id,  course_id,           course_name
    ('CAT_SN',  'CAT_SN_SC01',  '7음계'),
    ('CAT_SN',  'CAT_SN_SC02',  '12음계'),
    ('CAT_INT', 'CAT_INT_SC01', '코스1: 1도, 2도'),
    ('CAT_INT', 'CAT_INT_SC02', '코스2: 2도, 3도'),
    ('CAT_INT', 'CAT_INT_SC03', '코스3: 3도, 4도'),
    ('CAT_INT', 'CAT_INT_SC04', '코스4: 4도, 5도'),
    ('CAT_INT', 'CAT_INT_SC05', '코스5: 3도, 6도'),
    ('CAT_INT', 'CAT_INT_SC06', '코스6: 2도, 7도'),
]

PART_DATA = [
    # course_id,       part_id,               part_name,                              interval_pool
    # ── CAT_SN SC01: 7음계 ──────────────────────────────────────────────────────
    ('CAT_SN_SC01', 'CAT_SN_SC01_P01', '파트01 — C,F 구분',           ''),
    ('CAT_SN_SC01', 'CAT_SN_SC01_P02', '파트02 — C,F,G 구분',         ''),
    ('CAT_SN_SC01', 'CAT_SN_SC01_P03', '파트03 — C,D,F,G 구분',       ''),
    ('CAT_SN_SC01', 'CAT_SN_SC01_P04', '파트04 — C,D,E,F,G 구분',     ''),
    ('CAT_SN_SC01', 'CAT_SN_SC01_P05', '파트05 — C,D,E,F,G,A 구분',   ''),
    ('CAT_SN_SC01', 'CAT_SN_SC01_P06', '파트06 — C,D,E,F,G,A,B 구분', ''),
    # ── CAT_SN SC02: 12음계 ─────────────────────────────────────────────────────
    ('CAT_SN_SC02', 'CAT_SN_SC02_P01', '파트01 — F,F# 구분',                    ''),
    ('CAT_SN_SC02', 'CAT_SN_SC02_P02', '파트02 — C,C# 구분',                    ''),
    ('CAT_SN_SC02', 'CAT_SN_SC02_P03', '파트03 — C,C#,F,F# 구분',               ''),
    ('CAT_SN_SC02', 'CAT_SN_SC02_P04', '파트04 — G,G# 구분',                    ''),
    ('CAT_SN_SC02', 'CAT_SN_SC02_P05', '파트05 — C,C#,F,F#,G,G# 구분',          ''),
    ('CAT_SN_SC02', 'CAT_SN_SC02_P06', '파트06 — A,Bb,B 구분',                  ''),
    ('CAT_SN_SC02', 'CAT_SN_SC02_P07', '파트07 — C,C#,F,F#,G,G#,A,Bb,B 구분',  ''),
    ('CAT_SN_SC02', 'CAT_SN_SC02_P08', '파트08 — D,Eb,E 구분',                  ''),
    ('CAT_SN_SC02', 'CAT_SN_SC02_P09', '파트09 — 12음 전체 구분',                ''),
    # ── CAT_INT SC01~SC06 ───────────────────────────────────────────────────────
    ('CAT_INT_SC01', 'CAT_INT_SC01_P01', '파트01 — 완전1도, 장2도',        'P1,M2'),
    ('CAT_INT_SC01', 'CAT_INT_SC01_P02', '파트02 — 단2도, 장2도',          'm2,M2'),
    ('CAT_INT_SC01', 'CAT_INT_SC01_P03', '파트03 — 전체복습',              'P1,m2,M2'),
    ('CAT_INT_SC02', 'CAT_INT_SC02_P01', '파트01 — 장2도, 장3도',          'M2,M3'),
    ('CAT_INT_SC02', 'CAT_INT_SC02_P02', '파트02 — 장2도, 단3도',          'M2,m3'),
    ('CAT_INT_SC02', 'CAT_INT_SC02_P03', '파트03 — 단3도, 장3도',          'm3,M3'),
    ('CAT_INT_SC02', 'CAT_INT_SC02_P04', '파트04 — 전체복습',              'M2,m3,M3'),
    ('CAT_INT_SC03', 'CAT_INT_SC03_P01', '파트01 — 장3도, 완전4도',        'M3,P4'),
    ('CAT_INT_SC03', 'CAT_INT_SC03_P02', '파트02 — 단3도, 장3도, 완전4도', 'm3,M3,P4'),
    ('CAT_INT_SC03', 'CAT_INT_SC03_P03', '파트03 — 완전4도, 증4도',        'P4,A4'),
    ('CAT_INT_SC03', 'CAT_INT_SC03_P04', '파트04 — 전체복습',              'm3,M3,P4,A4'),
    ('CAT_INT_SC04', 'CAT_INT_SC04_P01', '파트01 — 완전4도, 완전5도',      'P4,P5'),
    ('CAT_INT_SC04', 'CAT_INT_SC04_P02', '파트02 — 증4도, 완전5도',        'A4,P5'),
    ('CAT_INT_SC04', 'CAT_INT_SC04_P03', '파트03 — 전체복습',              'P4,A4,P5'),
    ('CAT_INT_SC05', 'CAT_INT_SC05_P01', '파트01 — 장3도, 단6도',          'M3,m6'),
    ('CAT_INT_SC05', 'CAT_INT_SC05_P02', '파트02 — 단3도, 장6도',          'm3,M6'),
    ('CAT_INT_SC05', 'CAT_INT_SC05_P03', '파트03 — 단6도, 장6도',          'm6,M6'),
    ('CAT_INT_SC05', 'CAT_INT_SC05_P04', '파트04 — 전체복습',              'm3,M3,m6,M6'),
    ('CAT_INT_SC06', 'CAT_INT_SC06_P01', '파트01 — 장2도, 단7도',          'M2,m7'),
    ('CAT_INT_SC06', 'CAT_INT_SC06_P02', '파트02 — 단2도, 장7도',          'm2,M7'),
    ('CAT_INT_SC06', 'CAT_INT_SC06_P03', '파트03 — 단7도, 장7도',          'm7,M7'),
    ('CAT_INT_SC06', 'CAT_INT_SC06_P04', '파트04 — 전체복습',              'm2,M2,m7,M7'),
]

CURRICULUM_DATA = [
    # part_id,            step_id,                   step_name,       question_type,  note_pool,                             direction,    answer_type,     difficulty_level
    # ── CAT_SN SC01 ───────────────────────────────────────────────────────────────────────
    ('CAT_SN_SC01_P01', 'CAT_SN_SC01_P01_S01', '같음/다름',    'single_note', 'C,F',                           '-', 'same_diff',    1),
    ('CAT_SN_SC01_P01', 'CAT_SN_SC01_P01_S02', '악보',          'single_note', 'C,F',                           '-', 'name_2choice', 1),
    ('CAT_SN_SC01_P01', 'CAT_SN_SC01_P01_S03', '음이름',        'single_note', 'C,F',                           '-', 'name_2choice', 1),
    ('CAT_SN_SC01_P01', 'CAT_SN_SC01_P01_S04', '피아노주관식',  'single_note', 'C,F',                           '-', 'piano_subj',   1),
    ('CAT_SN_SC01_P02', 'CAT_SN_SC01_P02_S01', '같음/다름',    'single_note', 'C,F,G',                         '-', 'same_diff',    1),
    ('CAT_SN_SC01_P02', 'CAT_SN_SC01_P02_S02', '악보',          'single_note', 'C,F,G',                         '-', 'name_2choice', 1),
    ('CAT_SN_SC01_P02', 'CAT_SN_SC01_P02_S03', '음이름',        'single_note', 'C,F,G',                         '-', 'name_2choice', 1),
    ('CAT_SN_SC01_P02', 'CAT_SN_SC01_P02_S04', '피아노주관식',  'single_note', 'C,F,G',                         '-', 'piano_subj',   1),
    ('CAT_SN_SC01_P03', 'CAT_SN_SC01_P03_S01', '같음/다름',    'single_note', 'C,D,F,G',                       '-', 'same_diff',    1),
    ('CAT_SN_SC01_P03', 'CAT_SN_SC01_P03_S02', '악보',          'single_note', 'C,D,F,G',                       '-', 'name_2choice', 2),
    ('CAT_SN_SC01_P03', 'CAT_SN_SC01_P03_S03', '음이름',        'single_note', 'C,D,F,G',                       '-', 'name_2choice', 2),
    ('CAT_SN_SC01_P03', 'CAT_SN_SC01_P03_S04', '음이름(4지)',   'single_note', 'C,D,F,G',                       '-', 'name_4choice', 2),
    ('CAT_SN_SC01_P03', 'CAT_SN_SC01_P03_S05', '피아노주관식',  'single_note', 'C,D,F,G',                       '-', 'piano_subj',   2),
    ('CAT_SN_SC01_P04', 'CAT_SN_SC01_P04_S01', '같음/다름',    'single_note', 'C,D,E,F,G',                     '-', 'same_diff',    1),
    ('CAT_SN_SC01_P04', 'CAT_SN_SC01_P04_S02', '악보',          'single_note', 'C,D,E,F,G',                     '-', 'name_2choice', 2),
    ('CAT_SN_SC01_P04', 'CAT_SN_SC01_P04_S03', '음이름',        'single_note', 'C,D,E,F,G',                     '-', 'name_2choice', 2),
    ('CAT_SN_SC01_P04', 'CAT_SN_SC01_P04_S04', '음이름(4지)',   'single_note', 'C,D,E,F,G',                     '-', 'name_4choice', 2),
    ('CAT_SN_SC01_P04', 'CAT_SN_SC01_P04_S05', '피아노주관식',  'single_note', 'C,D,E,F,G',                     '-', 'piano_subj',   2),
    ('CAT_SN_SC01_P05', 'CAT_SN_SC01_P05_S01', '같음/다름',    'single_note', 'C,D,E,F,G,A',                   '-', 'same_diff',    2),
    ('CAT_SN_SC01_P05', 'CAT_SN_SC01_P05_S02', '악보',          'single_note', 'C,D,E,F,G,A',                   '-', 'name_2choice', 2),
    ('CAT_SN_SC01_P05', 'CAT_SN_SC01_P05_S03', '음이름',        'single_note', 'C,D,E,F,G,A',                   '-', 'name_2choice', 2),
    ('CAT_SN_SC01_P05', 'CAT_SN_SC01_P05_S04', '음이름(4지)',   'single_note', 'C,D,E,F,G,A',                   '-', 'name_4choice', 2),
    ('CAT_SN_SC01_P05', 'CAT_SN_SC01_P05_S05', '피아노주관식',  'single_note', 'C,D,E,F,G,A',                   '-', 'piano_subj',   2),
    ('CAT_SN_SC01_P06', 'CAT_SN_SC01_P06_S01', '같음/다름',    'single_note', 'C,D,E,F,G,A,B',                 '-', 'same_diff',    2),
    ('CAT_SN_SC01_P06', 'CAT_SN_SC01_P06_S02', '악보',          'single_note', 'C,D,E,F,G,A,B',                 '-', 'name_2choice', 3),
    ('CAT_SN_SC01_P06', 'CAT_SN_SC01_P06_S03', '음이름',        'single_note', 'C,D,E,F,G,A,B',                 '-', 'name_2choice', 3),
    ('CAT_SN_SC01_P06', 'CAT_SN_SC01_P06_S04', '음이름(4지)',   'single_note', 'C,D,E,F,G,A,B',                 '-', 'name_4choice', 3),
    ('CAT_SN_SC01_P06', 'CAT_SN_SC01_P06_S05', '피아노주관식',  'single_note', 'C,D,E,F,G,A,B',                 '-', 'piano_subj',   3),
    # ── CAT_SN SC02 ───────────────────────────────────────────────────────────────────────
    ('CAT_SN_SC02_P01', 'CAT_SN_SC02_P01_S01', '같음/다름',    'single_note', 'F,F#',                          '-', 'same_diff',    1),
    ('CAT_SN_SC02_P01', 'CAT_SN_SC02_P01_S02', '악보',          'single_note', 'F,F#',                          '-', 'name_2choice', 1),
    ('CAT_SN_SC02_P01', 'CAT_SN_SC02_P01_S03', '음이름',        'single_note', 'F,F#',                          '-', 'name_2choice', 1),
    ('CAT_SN_SC02_P01', 'CAT_SN_SC02_P01_S04', '피아노주관식',  'single_note', 'F,F#',                          '-', 'piano_subj',   1),
    ('CAT_SN_SC02_P02', 'CAT_SN_SC02_P02_S01', '같음/다름',    'single_note', 'C,C#',                          '-', 'same_diff',    1),
    ('CAT_SN_SC02_P02', 'CAT_SN_SC02_P02_S02', '악보',          'single_note', 'C,C#',                          '-', 'name_2choice', 1),
    ('CAT_SN_SC02_P02', 'CAT_SN_SC02_P02_S03', '음이름',        'single_note', 'C,C#',                          '-', 'name_2choice', 1),
    ('CAT_SN_SC02_P02', 'CAT_SN_SC02_P02_S04', '피아노주관식',  'single_note', 'C,C#',                          '-', 'piano_subj',   1),
    ('CAT_SN_SC02_P03', 'CAT_SN_SC02_P03_S01', '같음/다름',    'single_note', 'C,C#,F,F#',                     '-', 'same_diff',    1),
    ('CAT_SN_SC02_P03', 'CAT_SN_SC02_P03_S02', '악보',          'single_note', 'C,C#,F,F#',                     '-', 'name_2choice', 2),
    ('CAT_SN_SC02_P03', 'CAT_SN_SC02_P03_S03', '음이름',        'single_note', 'C,C#,F,F#',                     '-', 'name_2choice', 2),
    ('CAT_SN_SC02_P03', 'CAT_SN_SC02_P03_S04', '음이름(4지)',   'single_note', 'C,C#,F,F#',                     '-', 'name_4choice', 2),
    ('CAT_SN_SC02_P03', 'CAT_SN_SC02_P03_S05', '피아노주관식',  'single_note', 'C,C#,F,F#',                     '-', 'piano_subj',   2),
    ('CAT_SN_SC02_P04', 'CAT_SN_SC02_P04_S01', '같음/다름',    'single_note', 'G,G#',                          '-', 'same_diff',    1),
    ('CAT_SN_SC02_P04', 'CAT_SN_SC02_P04_S02', '악보',          'single_note', 'G,G#',                          '-', 'name_2choice', 1),
    ('CAT_SN_SC02_P04', 'CAT_SN_SC02_P04_S03', '음이름',        'single_note', 'G,G#',                          '-', 'name_2choice', 1),
    ('CAT_SN_SC02_P04', 'CAT_SN_SC02_P04_S04', '피아노주관식',  'single_note', 'G,G#',                          '-', 'piano_subj',   1),
    ('CAT_SN_SC02_P05', 'CAT_SN_SC02_P05_S01', '같음/다름',    'single_note', 'C,C#,F,F#,G,G#',                '-', 'same_diff',    2),
    ('CAT_SN_SC02_P05', 'CAT_SN_SC02_P05_S02', '악보',          'single_note', 'C,C#,F,F#,G,G#',                '-', 'name_2choice', 2),
    ('CAT_SN_SC02_P05', 'CAT_SN_SC02_P05_S03', '음이름',        'single_note', 'C,C#,F,F#,G,G#',                '-', 'name_2choice', 2),
    ('CAT_SN_SC02_P05', 'CAT_SN_SC02_P05_S04', '음이름(4지)',   'single_note', 'C,C#,F,F#,G,G#',                '-', 'name_4choice', 2),
    ('CAT_SN_SC02_P05', 'CAT_SN_SC02_P05_S05', '피아노주관식',  'single_note', 'C,C#,F,F#,G,G#',                '-', 'piano_subj',   2),
    ('CAT_SN_SC02_P06', 'CAT_SN_SC02_P06_S01', '같음/다름',    'single_note', 'A,Bb,B',                        '-', 'same_diff',    2),
    ('CAT_SN_SC02_P06', 'CAT_SN_SC02_P06_S02', '악보',          'single_note', 'A,Bb,B',                        '-', 'name_2choice', 2),
    ('CAT_SN_SC02_P06', 'CAT_SN_SC02_P06_S03', '음이름(3지)',   'single_note', 'A,Bb,B',                        '-', 'name_3choice', 2),
    ('CAT_SN_SC02_P06', 'CAT_SN_SC02_P06_S04', '피아노주관식',  'single_note', 'A,Bb,B',                        '-', 'piano_subj',   2),
    ('CAT_SN_SC02_P07', 'CAT_SN_SC02_P07_S01', '같음/다름',    'single_note', 'C,C#,F,F#,G,G#,A,Bb,B',         '-', 'same_diff',    2),
    ('CAT_SN_SC02_P07', 'CAT_SN_SC02_P07_S02', '악보',          'single_note', 'C,C#,F,F#,G,G#,A,Bb,B',         '-', 'name_2choice', 2),
    ('CAT_SN_SC02_P07', 'CAT_SN_SC02_P07_S03', '음이름',        'single_note', 'C,C#,F,F#,G,G#,A,Bb,B',         '-', 'name_2choice', 2),
    ('CAT_SN_SC02_P07', 'CAT_SN_SC02_P07_S04', '음이름(4지)',   'single_note', 'C,C#,F,F#,G,G#,A,Bb,B',         '-', 'name_4choice', 3),
    ('CAT_SN_SC02_P07', 'CAT_SN_SC02_P07_S05', '피아노주관식',  'single_note', 'C,C#,F,F#,G,G#,A,Bb,B',         '-', 'piano_subj',   3),
    ('CAT_SN_SC02_P08', 'CAT_SN_SC02_P08_S01', '같음/다름',    'single_note', 'D,Eb,E',                        '-', 'same_diff',    2),
    ('CAT_SN_SC02_P08', 'CAT_SN_SC02_P08_S02', '악보',          'single_note', 'D,Eb,E',                        '-', 'name_2choice', 2),
    ('CAT_SN_SC02_P08', 'CAT_SN_SC02_P08_S03', '음이름(3지)',   'single_note', 'D,Eb,E',                        '-', 'name_3choice', 2),
    ('CAT_SN_SC02_P08', 'CAT_SN_SC02_P08_S04', '피아노주관식',  'single_note', 'D,Eb,E',                        '-', 'piano_subj',   2),
    ('CAT_SN_SC02_P09', 'CAT_SN_SC02_P09_S01', '같음/다름',    'single_note', 'C,C#,D,Eb,E,F,F#,G,G#,A,Bb,B', '-', 'same_diff',    3),
    ('CAT_SN_SC02_P09', 'CAT_SN_SC02_P09_S02', '악보',          'single_note', 'C,C#,D,Eb,E,F,F#,G,G#,A,Bb,B', '-', 'name_2choice', 3),
    ('CAT_SN_SC02_P09', 'CAT_SN_SC02_P09_S03', '음이름',        'single_note', 'C,C#,D,Eb,E,F,F#,G,G#,A,Bb,B', '-', 'name_2choice', 3),
    ('CAT_SN_SC02_P09', 'CAT_SN_SC02_P09_S04', '음이름(4지)',   'single_note', 'C,C#,D,Eb,E,F,F#,G,G#,A,Bb,B', '-', 'name_4choice', 3),
    ('CAT_SN_SC02_P09', 'CAT_SN_SC02_P09_S05', '피아노주관식',  'single_note', 'C,C#,D,Eb,E,F,F#,G,G#,A,Bb,B', '-', 'piano_subj',   3),
    # ── CAT_INT SC01 ──────────────────────────────────────────────────────────────────────
    ('CAT_INT_SC01_P01', 'CAT_INT_SC01_P01_S01', '음정 같음/다름',       'interval', 'P1,M2', 'ascending',  'same_diff',     1),
    ('CAT_INT_SC01_P01', 'CAT_INT_SC01_P01_S02', '다양한 높이 비교',     'interval', 'P1,M2', 'ascending',  'height_compare',1),
    ('CAT_INT_SC01_P01', 'CAT_INT_SC01_P01_S03', '음정 이름 고르기',     'interval', 'P1,M2', 'ascending',  'name_2choice',  1),
    ('CAT_INT_SC01_P01', 'CAT_INT_SC01_P01_S04', '상행 음정 알아맞히기', 'interval', 'P1,M2', 'ascending',  'interval_subj', 1),
    ('CAT_INT_SC01_P01', 'CAT_INT_SC01_P01_S05', '하행 음정 알아맞히기', 'interval', 'P1,M2', 'descending', 'interval_subj', 1),
    ('CAT_INT_SC01_P01', 'CAT_INT_SC01_P01_S06', '건반에서 음정 선택',   'interval', 'P1,M2', 'ascending',  'keyboard_subj', 1),
    ('CAT_INT_SC01_P01', 'CAT_INT_SC01_P01_S07', '화음에서 음정 찾기',   'interval', 'P1,M2', 'harmonic',   'interval_subj', 1),
    ('CAT_INT_SC01_P02', 'CAT_INT_SC01_P02_S01', '음정 같음/다름',       'interval', 'm2,M2', 'ascending',  'same_diff',     1),
    ('CAT_INT_SC01_P02', 'CAT_INT_SC01_P02_S02', '다양한 높이 비교',     'interval', 'm2,M2', 'ascending',  'height_compare',1),
    ('CAT_INT_SC01_P02', 'CAT_INT_SC01_P02_S03', '음정 이름 고르기',     'interval', 'm2,M2', 'ascending',  'name_2choice',  1),
    ('CAT_INT_SC01_P02', 'CAT_INT_SC01_P02_S04', '상행 음정 알아맞히기', 'interval', 'm2,M2', 'ascending',  'interval_subj', 1),
    ('CAT_INT_SC01_P02', 'CAT_INT_SC01_P02_S05', '하행 음정 알아맞히기', 'interval', 'm2,M2', 'descending', 'interval_subj', 1),
    ('CAT_INT_SC01_P02', 'CAT_INT_SC01_P02_S06', '건반에서 음정 선택',   'interval', 'm2,M2', 'ascending',  'keyboard_subj', 1),
    ('CAT_INT_SC01_P02', 'CAT_INT_SC01_P02_S07', '화음에서 음정 찾기',   'interval', 'm2,M2', 'harmonic',   'interval_subj', 1),
    ('CAT_INT_SC01_P03', 'CAT_INT_SC01_P03_S01', '음정 이름 고르기',     'interval', 'P1,m2,M2', 'ascending',  'name_3choice',  2),
    ('CAT_INT_SC01_P03', 'CAT_INT_SC01_P03_S02', '상행 음정 알아맞히기', 'interval', 'P1,m2,M2', 'ascending',  'interval_subj', 2),
    ('CAT_INT_SC01_P03', 'CAT_INT_SC01_P03_S03', '하행 음정 알아맞히기', 'interval', 'P1,m2,M2', 'descending', 'interval_subj', 2),
    ('CAT_INT_SC01_P03', 'CAT_INT_SC01_P03_S04', '건반에서 음정 선택',   'interval', 'P1,m2,M2', 'ascending',  'keyboard_subj', 2),
    ('CAT_INT_SC01_P03', 'CAT_INT_SC01_P03_S05', '화음에서 음정 찾기',   'interval', 'P1,m2,M2', 'harmonic',   'interval_subj', 2),
    # ── CAT_INT SC02 ──────────────────────────────────────────────────────────────────────
    ('CAT_INT_SC02_P01', 'CAT_INT_SC02_P01_S01', '음정 같음/다름',       'interval', 'M2,M3', 'ascending',  'same_diff',     1),
    ('CAT_INT_SC02_P01', 'CAT_INT_SC02_P01_S02', '다양한 높이 비교',     'interval', 'M2,M3', 'ascending',  'height_compare',1),
    ('CAT_INT_SC02_P01', 'CAT_INT_SC02_P01_S03', '음정 이름 고르기',     'interval', 'M2,M3', 'ascending',  'name_2choice',  1),
    ('CAT_INT_SC02_P01', 'CAT_INT_SC02_P01_S04', '상행 음정 알아맞히기', 'interval', 'M2,M3', 'ascending',  'interval_subj', 1),
    ('CAT_INT_SC02_P01', 'CAT_INT_SC02_P01_S05', '하행 음정 알아맞히기', 'interval', 'M2,M3', 'descending', 'interval_subj', 1),
    ('CAT_INT_SC02_P01', 'CAT_INT_SC02_P01_S06', '건반에서 음정 선택',   'interval', 'M2,M3', 'ascending',  'keyboard_subj', 1),
    ('CAT_INT_SC02_P01', 'CAT_INT_SC02_P01_S07', '화음에서 음정 찾기',   'interval', 'M2,M3', 'harmonic',   'interval_subj', 1),
    ('CAT_INT_SC02_P02', 'CAT_INT_SC02_P02_S01', '음정 같음/다름',       'interval', 'M2,m3', 'ascending',  'same_diff',     1),
    ('CAT_INT_SC02_P02', 'CAT_INT_SC02_P02_S02', '다양한 높이 비교',     'interval', 'M2,m3', 'ascending',  'height_compare',1),
    ('CAT_INT_SC02_P02', 'CAT_INT_SC02_P02_S03', '음정 이름 고르기',     'interval', 'M2,m3', 'ascending',  'name_2choice',  1),
    ('CAT_INT_SC02_P02', 'CAT_INT_SC02_P02_S04', '상행 음정 알아맞히기', 'interval', 'M2,m3', 'ascending',  'interval_subj', 1),
    ('CAT_INT_SC02_P02', 'CAT_INT_SC02_P02_S05', '하행 음정 알아맞히기', 'interval', 'M2,m3', 'descending', 'interval_subj', 1),
    ('CAT_INT_SC02_P02', 'CAT_INT_SC02_P02_S06', '건반에서 음정 선택',   'interval', 'M2,m3', 'ascending',  'keyboard_subj', 1),
    ('CAT_INT_SC02_P02', 'CAT_INT_SC02_P02_S07', '화음에서 음정 찾기',   'interval', 'M2,m3', 'harmonic',   'interval_subj', 1),
    ('CAT_INT_SC02_P03', 'CAT_INT_SC02_P03_S01', '음정 같음/다름',       'interval', 'm3,M3', 'ascending',  'same_diff',     1),
    ('CAT_INT_SC02_P03', 'CAT_INT_SC02_P03_S02', '다양한 높이 비교',     'interval', 'm3,M3', 'ascending',  'height_compare',1),
    ('CAT_INT_SC02_P03', 'CAT_INT_SC02_P03_S03', '음정 이름 고르기',     'interval', 'm3,M3', 'ascending',  'name_2choice',  1),
    ('CAT_INT_SC02_P03', 'CAT_INT_SC02_P03_S04', '상행 음정 알아맞히기', 'interval', 'm3,M3', 'ascending',  'interval_subj', 1),
    ('CAT_INT_SC02_P03', 'CAT_INT_SC02_P03_S05', '하행 음정 알아맞히기', 'interval', 'm3,M3', 'descending', 'interval_subj', 1),
    ('CAT_INT_SC02_P03', 'CAT_INT_SC02_P03_S06', '건반에서 음정 선택',   'interval', 'm3,M3', 'ascending',  'keyboard_subj', 1),
    ('CAT_INT_SC02_P03', 'CAT_INT_SC02_P03_S07', '화음에서 음정 찾기',   'interval', 'm3,M3', 'harmonic',   'interval_subj', 1),
    ('CAT_INT_SC02_P04', 'CAT_INT_SC02_P04_S01', '음정 이름 고르기',     'interval', 'M2,m3,M3', 'ascending',  'name_3choice',  2),
    ('CAT_INT_SC02_P04', 'CAT_INT_SC02_P04_S02', '상행 음정 알아맞히기', 'interval', 'M2,m3,M3', 'ascending',  'interval_subj', 2),
    ('CAT_INT_SC02_P04', 'CAT_INT_SC02_P04_S03', '하행 음정 알아맞히기', 'interval', 'M2,m3,M3', 'descending', 'interval_subj', 2),
    ('CAT_INT_SC02_P04', 'CAT_INT_SC02_P04_S04', '건반에서 음정 선택',   'interval', 'M2,m3,M3', 'ascending',  'keyboard_subj', 2),
    ('CAT_INT_SC02_P04', 'CAT_INT_SC02_P04_S05', '화음에서 음정 찾기',   'interval', 'M2,m3,M3', 'harmonic',   'interval_subj', 2),
    # ── CAT_INT SC03 ──────────────────────────────────────────────────────────────────────
    ('CAT_INT_SC03_P01', 'CAT_INT_SC03_P01_S01', '음정 같음/다름',       'interval', 'M3,P4',       'ascending',  'same_diff',     1),
    ('CAT_INT_SC03_P01', 'CAT_INT_SC03_P01_S02', '다양한 높이 비교',     'interval', 'M3,P4',       'ascending',  'height_compare',1),
    ('CAT_INT_SC03_P01', 'CAT_INT_SC03_P01_S03', '음정 이름 고르기',     'interval', 'M3,P4',       'ascending',  'name_2choice',  1),
    ('CAT_INT_SC03_P01', 'CAT_INT_SC03_P01_S04', '상행 음정 알아맞히기', 'interval', 'M3,P4',       'ascending',  'interval_subj', 1),
    ('CAT_INT_SC03_P01', 'CAT_INT_SC03_P01_S05', '하행 음정 알아맞히기', 'interval', 'M3,P4',       'descending', 'interval_subj', 1),
    ('CAT_INT_SC03_P01', 'CAT_INT_SC03_P01_S06', '건반에서 음정 선택',   'interval', 'M3,P4',       'ascending',  'keyboard_subj', 1),
    ('CAT_INT_SC03_P01', 'CAT_INT_SC03_P01_S07', '화음에서 음정 찾기',   'interval', 'M3,P4',       'harmonic',   'interval_subj', 1),
    ('CAT_INT_SC03_P02', 'CAT_INT_SC03_P02_S01', '음정 같음/다름',       'interval', 'm3,M3,P4',    'ascending',  'same_diff',     2),
    ('CAT_INT_SC03_P02', 'CAT_INT_SC03_P02_S02', '다양한 높이 비교',     'interval', 'm3,M3,P4',    'ascending',  'height_compare',2),
    ('CAT_INT_SC03_P02', 'CAT_INT_SC03_P02_S03', '음정 이름 고르기',     'interval', 'm3,M3,P4',    'ascending',  'name_3choice',  2),
    ('CAT_INT_SC03_P02', 'CAT_INT_SC03_P02_S04', '상행 음정 알아맞히기', 'interval', 'm3,M3,P4',    'ascending',  'interval_subj', 2),
    ('CAT_INT_SC03_P02', 'CAT_INT_SC03_P02_S05', '하행 음정 알아맞히기', 'interval', 'm3,M3,P4',    'descending', 'interval_subj', 2),
    ('CAT_INT_SC03_P02', 'CAT_INT_SC03_P02_S06', '건반에서 음정 선택',   'interval', 'm3,M3,P4',    'ascending',  'keyboard_subj', 2),
    ('CAT_INT_SC03_P02', 'CAT_INT_SC03_P02_S07', '화음에서 음정 찾기',   'interval', 'm3,M3,P4',    'harmonic',   'interval_subj', 2),
    ('CAT_INT_SC03_P03', 'CAT_INT_SC03_P03_S01', '음정 같음/다름',       'interval', 'P4,A4',       'ascending',  'same_diff',     2),
    ('CAT_INT_SC03_P03', 'CAT_INT_SC03_P03_S02', '다양한 높이 비교',     'interval', 'P4,A4',       'ascending',  'height_compare',2),
    ('CAT_INT_SC03_P03', 'CAT_INT_SC03_P03_S03', '음정 이름 고르기',     'interval', 'P4,A4',       'ascending',  'name_2choice',  2),
    ('CAT_INT_SC03_P03', 'CAT_INT_SC03_P03_S04', '상행 음정 알아맞히기', 'interval', 'P4,A4',       'ascending',  'interval_subj', 2),
    ('CAT_INT_SC03_P03', 'CAT_INT_SC03_P03_S05', '하행 음정 알아맞히기', 'interval', 'P4,A4',       'descending', 'interval_subj', 2),
    ('CAT_INT_SC03_P03', 'CAT_INT_SC03_P03_S06', '건반에서 음정 선택',   'interval', 'P4,A4',       'ascending',  'keyboard_subj', 2),
    ('CAT_INT_SC03_P03', 'CAT_INT_SC03_P03_S07', '화음에서 음정 찾기',   'interval', 'P4,A4',       'harmonic',   'interval_subj', 2),
    ('CAT_INT_SC03_P04', 'CAT_INT_SC03_P04_S01', '음정 이름 고르기',     'interval', 'm3,M3,P4,A4', 'ascending',  'name_4choice',  2),
    ('CAT_INT_SC03_P04', 'CAT_INT_SC03_P04_S02', '상행 음정 알아맞히기', 'interval', 'm3,M3,P4,A4', 'ascending',  'interval_subj', 2),
    ('CAT_INT_SC03_P04', 'CAT_INT_SC03_P04_S03', '하행 음정 알아맞히기', 'interval', 'm3,M3,P4,A4', 'descending', 'interval_subj', 2),
    ('CAT_INT_SC03_P04', 'CAT_INT_SC03_P04_S04', '건반에서 음정 선택',   'interval', 'm3,M3,P4,A4', 'ascending',  'keyboard_subj', 2),
    ('CAT_INT_SC03_P04', 'CAT_INT_SC03_P04_S05', '화음에서 음정 찾기',   'interval', 'm3,M3,P4,A4', 'harmonic',   'interval_subj', 2),
    # ── CAT_INT SC04 ──────────────────────────────────────────────────────────────────────
    ('CAT_INT_SC04_P01', 'CAT_INT_SC04_P01_S01', '음정 같음/다름',       'interval', 'P4,P5',    'ascending',  'same_diff',     2),
    ('CAT_INT_SC04_P01', 'CAT_INT_SC04_P01_S02', '다양한 높이 비교',     'interval', 'P4,P5',    'ascending',  'height_compare',2),
    ('CAT_INT_SC04_P01', 'CAT_INT_SC04_P01_S03', '음정 이름 고르기',     'interval', 'P4,P5',    'ascending',  'name_2choice',  2),
    ('CAT_INT_SC04_P01', 'CAT_INT_SC04_P01_S04', '상행 음정 알아맞히기', 'interval', 'P4,P5',    'ascending',  'interval_subj', 2),
    ('CAT_INT_SC04_P01', 'CAT_INT_SC04_P01_S05', '하행 음정 알아맞히기', 'interval', 'P4,P5',    'descending', 'interval_subj', 2),
    ('CAT_INT_SC04_P01', 'CAT_INT_SC04_P01_S06', '건반에서 음정 선택',   'interval', 'P4,P5',    'ascending',  'keyboard_subj', 2),
    ('CAT_INT_SC04_P01', 'CAT_INT_SC04_P01_S07', '화음에서 음정 찾기',   'interval', 'P4,P5',    'harmonic',   'interval_subj', 2),
    ('CAT_INT_SC04_P02', 'CAT_INT_SC04_P02_S01', '음정 같음/다름',       'interval', 'A4,P5',    'ascending',  'same_diff',     2),
    ('CAT_INT_SC04_P02', 'CAT_INT_SC04_P02_S02', '다양한 높이 비교',     'interval', 'A4,P5',    'ascending',  'height_compare',2),
    ('CAT_INT_SC04_P02', 'CAT_INT_SC04_P02_S03', '음정 이름 고르기',     'interval', 'A4,P5',    'ascending',  'name_2choice',  2),
    ('CAT_INT_SC04_P02', 'CAT_INT_SC04_P02_S04', '상행 음정 알아맞히기', 'interval', 'A4,P5',    'ascending',  'interval_subj', 2),
    ('CAT_INT_SC04_P02', 'CAT_INT_SC04_P02_S05', '하행 음정 알아맞히기', 'interval', 'A4,P5',    'descending', 'interval_subj', 2),
    ('CAT_INT_SC04_P02', 'CAT_INT_SC04_P02_S06', '건반에서 음정 선택',   'interval', 'A4,P5',    'ascending',  'keyboard_subj', 2),
    ('CAT_INT_SC04_P02', 'CAT_INT_SC04_P02_S07', '화음에서 음정 찾기',   'interval', 'A4,P5',    'harmonic',   'interval_subj', 2),
    ('CAT_INT_SC04_P03', 'CAT_INT_SC04_P03_S01', '음정 이름 고르기',     'interval', 'P4,A4,P5', 'ascending',  'name_3choice',  2),
    ('CAT_INT_SC04_P03', 'CAT_INT_SC04_P03_S02', '상행 음정 알아맞히기', 'interval', 'P4,A4,P5', 'ascending',  'interval_subj', 2),
    ('CAT_INT_SC04_P03', 'CAT_INT_SC04_P03_S03', '하행 음정 알아맞히기', 'interval', 'P4,A4,P5', 'descending', 'interval_subj', 2),
    ('CAT_INT_SC04_P03', 'CAT_INT_SC04_P03_S04', '건반에서 음정 선택',   'interval', 'P4,A4,P5', 'ascending',  'keyboard_subj', 2),
    ('CAT_INT_SC04_P03', 'CAT_INT_SC04_P03_S05', '화음에서 음정 찾기',   'interval', 'P4,A4,P5', 'harmonic',   'interval_subj', 2),
    # ── CAT_INT SC05 ──────────────────────────────────────────────────────────────────────
    ('CAT_INT_SC05_P01', 'CAT_INT_SC05_P01_S01', '음정 같음/다름',       'interval', 'M3,m6',       'ascending',  'same_diff',     2),
    ('CAT_INT_SC05_P01', 'CAT_INT_SC05_P01_S02', '다양한 높이 비교',     'interval', 'M3,m6',       'ascending',  'height_compare',2),
    ('CAT_INT_SC05_P01', 'CAT_INT_SC05_P01_S03', '음정 이름 고르기',     'interval', 'M3,m6',       'ascending',  'name_2choice',  2),
    ('CAT_INT_SC05_P01', 'CAT_INT_SC05_P01_S04', '상행 음정 알아맞히기', 'interval', 'M3,m6',       'ascending',  'interval_subj', 2),
    ('CAT_INT_SC05_P01', 'CAT_INT_SC05_P01_S05', '하행 음정 알아맞히기', 'interval', 'M3,m6',       'descending', 'interval_subj', 2),
    ('CAT_INT_SC05_P01', 'CAT_INT_SC05_P01_S06', '건반에서 음정 선택',   'interval', 'M3,m6',       'ascending',  'keyboard_subj', 2),
    ('CAT_INT_SC05_P01', 'CAT_INT_SC05_P01_S07', '화음에서 음정 찾기',   'interval', 'M3,m6',       'harmonic',   'interval_subj', 2),
    ('CAT_INT_SC05_P02', 'CAT_INT_SC05_P02_S01', '음정 같음/다름',       'interval', 'm3,M6',       'ascending',  'same_diff',     2),
    ('CAT_INT_SC05_P02', 'CAT_INT_SC05_P02_S02', '다양한 높이 비교',     'interval', 'm3,M6',       'ascending',  'height_compare',2),
    ('CAT_INT_SC05_P02', 'CAT_INT_SC05_P02_S03', '음정 이름 고르기',     'interval', 'm3,M6',       'ascending',  'name_2choice',  2),
    ('CAT_INT_SC05_P02', 'CAT_INT_SC05_P02_S04', '상행 음정 알아맞히기', 'interval', 'm3,M6',       'ascending',  'interval_subj', 2),
    ('CAT_INT_SC05_P02', 'CAT_INT_SC05_P02_S05', '하행 음정 알아맞히기', 'interval', 'm3,M6',       'descending', 'interval_subj', 2),
    ('CAT_INT_SC05_P02', 'CAT_INT_SC05_P02_S06', '건반에서 음정 선택',   'interval', 'm3,M6',       'ascending',  'keyboard_subj', 2),
    ('CAT_INT_SC05_P02', 'CAT_INT_SC05_P02_S07', '화음에서 음정 찾기',   'interval', 'm3,M6',       'harmonic',   'interval_subj', 2),
    ('CAT_INT_SC05_P03', 'CAT_INT_SC05_P03_S01', '음정 같음/다름',       'interval', 'm6,M6',       'ascending',  'same_diff',     2),
    ('CAT_INT_SC05_P03', 'CAT_INT_SC05_P03_S02', '다양한 높이 비교',     'interval', 'm6,M6',       'ascending',  'height_compare',2),
    ('CAT_INT_SC05_P03', 'CAT_INT_SC05_P03_S03', '음정 이름 고르기',     'interval', 'm6,M6',       'ascending',  'name_2choice',  2),
    ('CAT_INT_SC05_P03', 'CAT_INT_SC05_P03_S04', '상행 음정 알아맞히기', 'interval', 'm6,M6',       'ascending',  'interval_subj', 2),
    ('CAT_INT_SC05_P03', 'CAT_INT_SC05_P03_S05', '하행 음정 알아맞히기', 'interval', 'm6,M6',       'descending', 'interval_subj', 2),
    ('CAT_INT_SC05_P03', 'CAT_INT_SC05_P03_S06', '건반에서 음정 선택',   'interval', 'm6,M6',       'ascending',  'keyboard_subj', 2),
    ('CAT_INT_SC05_P03', 'CAT_INT_SC05_P03_S07', '화음에서 음정 찾기',   'interval', 'm6,M6',       'harmonic',   'interval_subj', 2),
    ('CAT_INT_SC05_P04', 'CAT_INT_SC05_P04_S01', '음정 이름 고르기',     'interval', 'm3,M3,m6,M6', 'ascending',  'name_4choice',  3),
    ('CAT_INT_SC05_P04', 'CAT_INT_SC05_P04_S02', '상행 음정 알아맞히기', 'interval', 'm3,M3,m6,M6', 'ascending',  'interval_subj', 3),
    ('CAT_INT_SC05_P04', 'CAT_INT_SC05_P04_S03', '하행 음정 알아맞히기', 'interval', 'm3,M3,m6,M6', 'descending', 'interval_subj', 3),
    ('CAT_INT_SC05_P04', 'CAT_INT_SC05_P04_S04', '건반에서 음정 선택',   'interval', 'm3,M3,m6,M6', 'ascending',  'keyboard_subj', 3),
    ('CAT_INT_SC05_P04', 'CAT_INT_SC05_P04_S05', '화음에서 음정 찾기',   'interval', 'm3,M3,m6,M6', 'harmonic',   'interval_subj', 3),
    # ── CAT_INT SC06 ──────────────────────────────────────────────────────────────────────
    ('CAT_INT_SC06_P01', 'CAT_INT_SC06_P01_S01', '음정 같음/다름',       'interval', 'M2,m7',       'ascending',  'same_diff',     2),
    ('CAT_INT_SC06_P01', 'CAT_INT_SC06_P01_S02', '다양한 높이 비교',     'interval', 'M2,m7',       'ascending',  'height_compare',2),
    ('CAT_INT_SC06_P01', 'CAT_INT_SC06_P01_S03', '음정 이름 고르기',     'interval', 'M2,m7',       'ascending',  'name_2choice',  2),
    ('CAT_INT_SC06_P01', 'CAT_INT_SC06_P01_S04', '상행 음정 알아맞히기', 'interval', 'M2,m7',       'ascending',  'interval_subj', 2),
    ('CAT_INT_SC06_P01', 'CAT_INT_SC06_P01_S05', '하행 음정 알아맞히기', 'interval', 'M2,m7',       'descending', 'interval_subj', 2),
    ('CAT_INT_SC06_P01', 'CAT_INT_SC06_P01_S06', '건반에서 음정 선택',   'interval', 'M2,m7',       'ascending',  'keyboard_subj', 2),
    ('CAT_INT_SC06_P01', 'CAT_INT_SC06_P01_S07', '화음에서 음정 찾기',   'interval', 'M2,m7',       'harmonic',   'interval_subj', 2),
    ('CAT_INT_SC06_P02', 'CAT_INT_SC06_P02_S01', '음정 같음/다름',       'interval', 'm2,M7',       'ascending',  'same_diff',     2),
    ('CAT_INT_SC06_P02', 'CAT_INT_SC06_P02_S02', '다양한 높이 비교',     'interval', 'm2,M7',       'ascending',  'height_compare',2),
    ('CAT_INT_SC06_P02', 'CAT_INT_SC06_P02_S03', '음정 이름 고르기',     'interval', 'm2,M7',       'ascending',  'name_2choice',  2),
    ('CAT_INT_SC06_P02', 'CAT_INT_SC06_P02_S04', '상행 음정 알아맞히기', 'interval', 'm2,M7',       'ascending',  'interval_subj', 2),
    ('CAT_INT_SC06_P02', 'CAT_INT_SC06_P02_S05', '하행 음정 알아맞히기', 'interval', 'm2,M7',       'descending', 'interval_subj', 2),
    ('CAT_INT_SC06_P02', 'CAT_INT_SC06_P02_S06', '건반에서 음정 선택',   'interval', 'm2,M7',       'ascending',  'keyboard_subj', 2),
    ('CAT_INT_SC06_P02', 'CAT_INT_SC06_P02_S07', '화음에서 음정 찾기',   'interval', 'm2,M7',       'harmonic',   'interval_subj', 2),
    ('CAT_INT_SC06_P03', 'CAT_INT_SC06_P03_S01', '음정 같음/다름',       'interval', 'm7,M7',       'ascending',  'same_diff',     2),
    ('CAT_INT_SC06_P03', 'CAT_INT_SC06_P03_S02', '다양한 높이 비교',     'interval', 'm7,M7',       'ascending',  'height_compare',2),
    ('CAT_INT_SC06_P03', 'CAT_INT_SC06_P03_S03', '음정 이름 고르기',     'interval', 'm7,M7',       'ascending',  'name_2choice',  2),
    ('CAT_INT_SC06_P03', 'CAT_INT_SC06_P03_S04', '상행 음정 알아맞히기', 'interval', 'm7,M7',       'ascending',  'interval_subj', 2),
    ('CAT_INT_SC06_P03', 'CAT_INT_SC06_P03_S05', '하행 음정 알아맞히기', 'interval', 'm7,M7',       'descending', 'interval_subj', 2),
    ('CAT_INT_SC06_P03', 'CAT_INT_SC06_P03_S06', '건반에서 음정 선택',   'interval', 'm7,M7',       'ascending',  'keyboard_subj', 2),
    ('CAT_INT_SC06_P03', 'CAT_INT_SC06_P03_S07', '화음에서 음정 찾기',   'interval', 'm7,M7',       'harmonic',   'interval_subj', 2),
    ('CAT_INT_SC06_P04', 'CAT_INT_SC06_P04_S01', '음정 이름 고르기',     'interval', 'm2,M2,m7,M7', 'ascending',  'name_4choice',  3),
    ('CAT_INT_SC06_P04', 'CAT_INT_SC06_P04_S02', '상행 음정 알아맞히기', 'interval', 'm2,M2,m7,M7', 'ascending',  'interval_subj', 3),
    ('CAT_INT_SC06_P04', 'CAT_INT_SC06_P04_S03', '하행 음정 알아맞히기', 'interval', 'm2,M2,m7,M7', 'descending', 'interval_subj', 3),
    ('CAT_INT_SC06_P04', 'CAT_INT_SC06_P04_S04', '건반에서 음정 선택',   'interval', 'm2,M2,m7,M7', 'ascending',  'keyboard_subj', 3),
    ('CAT_INT_SC06_P04', 'CAT_INT_SC06_P04_S05', '화음에서 음정 찾기',   'interval', 'm2,M2,m7,M7', 'harmonic',   'interval_subj', 3),
]

CURRICULUM_COLS = ['part_id', 'step_id', 'step_name', 'question_type',
                   'note_pool', 'direction', 'answer_type', 'difficulty_level']

# O(1) 조회 딕셔너리 빌드
STEP_LOOKUP: dict = {r[1]: dict(zip(CURRICULUM_COLS, r)) for r in CURRICULUM_DATA}
ALL_STEP_IDS: list = [r[1] for r in CURRICULUM_DATA]


# ══════════════════════════════════════════════════════════════════════════════
# 3. Answer Type & Difficulty 규칙
# ══════════════════════════════════════════════════════════════════════════════
ANSWER_TYPE_RULES: dict = {
    # answer_type        label               num_choices  present_count  distractor_strategy   pool_size_rule
    'same_diff':        ('같음/다름',             2,           2,         'none',              '풀 크기 무관'),
    'name_2choice':     ('이름 2지선다',           2,           1,         'asc_by_distance',   '풀≤2:use_all / 풀≥3:asc_by_dist'),
    'name_3choice':     ('이름 3지선다',           3,           1,         'use_all',           '풀=3 전용'),
    'name_4choice':     ('이름 4지선다',           4,           1,         'asc_by_distance',   '풀≥4 전용'),
    'height_compare':   ('다양한 높이 비교',        2,           2,         'none',              '음정: 같은 음정 다른 높이'),
    'interval_subj':    ('음정 주관식',            0,           1,         'none',              '음정: direction 컬럼으로 상행/하행/화음 구분'),
    'keyboard_subj':    ('건반 선택',              0,           1,         'none',              '음정: 음정이름 제시→건반 선택'),
    'piano_subj':       ('피아노 주관식',           0,           1,         'none',              '단일음: 피아노 건반 직접 입력'),
}

DIFFICULTY_RULES: dict = {
    # level: (label, octaves, proximity_strategy, proximity_semitones)
    # rules.md 2-1: 쉬움=4옥타브만, 보통=3또는5옥타브(4제외), 어려움=3~6옥타브
    1: ('쉬움',   [4],            'desc_by_distance', '≥5반음/≥4반음차(오답 멀리)'),
    2: ('보통',   [3, 5],         'shuffle',           '무작위 배치'),
    3: ('어려움', [3, 4, 5, 6],   'asc_by_distance',  '≤2반음/≤1반음차(오답 가까이)'),
}


# ══════════════════════════════════════════════════════════════════════════════
# 4. 음 유틸 (MIDI ↔ 음이름 변환)
# ══════════════════════════════════════════════════════════════════════════════
NOTE_NAMES: list = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'G#', 'A', 'Bb', 'B']

ENHARMONIC_MAP: dict = {
    'Db': 'C#', 'D#': 'Eb', 'Gb': 'F#',
    'Ab': 'G#', 'A#': 'Bb', 'Cb': 'B', 'E#': 'F',
}

INTERVAL_SEMITONES: dict = {
    'P1': ('완전1도',  0),
    'm2': ('단2도',    1),
    'M2': ('장2도',    2),
    'm3': ('단3도',    3),
    'M3': ('장3도',    4),
    'P4': ('완전4도',  5),
    'A4': ('증4도',    6),
    'P5': ('완전5도',  7),
    'm6': ('단6도',    8),
    'M6': ('장6도',    9),
    'm7': ('단7도',   10),
    'M7': ('장7도',   11),
}


def normalize_note_name(name: str) -> str:
    return ENHARMONIC_MAP.get(name, name)


def note_to_midi(note_with_octave: str) -> int:
    octave = int(note_with_octave[-1])
    name = normalize_note_name(note_with_octave[:-1])
    pitch_class = NOTE_NAMES.index(name)
    return (octave + 1) * 12 + pitch_class


def midi_to_note(midi: int) -> str:
    return f"{NOTE_NAMES[midi % 12]}{(midi // 12) - 1}"


def parse_pool(pool_str: str) -> list:
    return [normalize_note_name(n.strip()) for n in pool_str.split(',')]


def pool_to_midi_range(pool: list, octaves: list) -> list:
    return sorted(
        note_to_midi(f'{name}{oct}')
        for oct in octaves
        for name in pool
        if MIDI_MIN <= note_to_midi(f'{name}{oct}') <= MIDI_MAX
    )


def semitone_distance(midi_a: int, midi_b: int) -> int:
    return abs(midi_a - midi_b)


def parse_interval_pool(pool_str: str) -> list:
    return [s.strip() for s in pool_str.split(',')]


def interval_semitones(symbol: str) -> int:
    return INTERVAL_SEMITONES[symbol][1]


def interval_name_ko(symbol: str) -> str:
    return INTERVAL_SEMITONES[symbol][0]


def build_interval_midi(root_midi: int, symbol: str, direction: str) -> int:
    st = interval_semitones(symbol)
    if direction == 'descending':
        return root_midi - st
    return root_midi + st


def interval_to_midi_pair(root_midi: int, symbol: str, direction: str) -> tuple:
    st = interval_semitones(symbol)
    if direction == 'descending':
        return (root_midi - st, root_midi)
    return (root_midi, root_midi + st)


def root_midi_pool(octaves: list) -> list:
    return [
        note_to_midi(f'{n}{o}')
        for o in octaves
        for n in NOTE_NAMES
        if MIDI_MIN <= note_to_midi(f'{n}{o}') <= MIDI_MAX
    ]


# ══════════════════════════════════════════════════════════════════════════════
# 5. SingleNoteGenerator
# ══════════════════════════════════════════════════════════════════════════════
class SingleNoteGenerator:
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self._session_history: dict = {}

    def generate(self, step_id: str, difficulty_level: int) -> dict:
        step    = STEP_LOOKUP[step_id]
        at_rule = self._get_answer_rule(step['answer_type'])
        d_rule  = self._get_difficulty_rule(difficulty_level)

        pool      = parse_pool(step['note_pool'])
        midi_pool = pool_to_midi_range(pool, d_rule['octaves'])
        answer_midi = self._pick_answer(step_id, midi_pool)
        answer      = midi_to_note(answer_midi)
        answer_type = step['answer_type']

        if answer_type == 'same_diff':
            # present_notes: 제시된 두 음 / answer: '같음' 또는 '다름' / choices: ['같음','다름']
            present_notes, same_diff_label = self._build_same_diff(
                answer_midi, pool, d_rule['octaves']
            )
            answer  = same_diff_label
            choices = ['같음', '다름']
        elif answer_type == 'piano_subj':
            present_notes, choices = [answer], None
        else:
            present_notes = [answer]
            choices = self._build_choices(
                answer_midi, pool,
                d_rule['octaves'],
                at_rule['num_choices'],
                at_rule['distractor_strategy'],
                d_rule['proximity_strategy'],
            )

        self._session_history.setdefault(step_id, []).append(answer_midi)

        return {
            'step_id':          step_id,
            'step_name':        step['step_name'],
            'question_type':    'single_note',
            'answer_type':      answer_type,
            'direction':        '-',
            'difficulty_level': difficulty_level,
            'answer':           answer,
            'answer_midi':      answer_midi,
            'present_notes':    present_notes,
            'choices':          choices,
            'total_difficulty': float(difficulty_level),
        }

    def reset_session(self):
        self._session_history = {}

    def _get_answer_rule(self, answer_type: str) -> dict:
        keys = ['label', 'num_choices', 'present_count', 'distractor_strategy', 'pool_size_rule']
        return dict(zip(keys, ANSWER_TYPE_RULES[answer_type]))

    def _get_difficulty_rule(self, level: int) -> dict:
        keys = ['label', 'octaves', 'proximity_strategy', 'proximity_semitones']
        return dict(zip(keys, DIFFICULTY_RULES[level]))

    def _pick_answer(self, step_id: str, midi_pool: list) -> int:
        # rules.md 3-4: 같은 정답 3회 연속 방지
        history = self._session_history.get(step_id, [])
        excluded = set()
        if len(history) >= 2 and history[-1] == history[-2]:
            excluded.add(history[-1])
        candidates = [m for m in midi_pool if m not in excluded]
        if not candidates:
            candidates = midi_pool
        return self.rng.choice(candidates)

    def _build_same_diff(self, answer_midi, pool, octaves):
        first   = midi_to_note(answer_midi)
        is_same = self.rng.choice([True, False])
        if is_same:
            second, label = first, '같음'
        else:
            answer_name = first[:-1]
            # 두 번째 제시음: 다른 음이름 & 첫 번째 음 기준 1옥타브 이내 (12반음)
            others = [
                m for m in pool_to_midi_range(pool, [3, 4, 5, 6])
                if midi_to_note(m)[:-1] != answer_name
                and abs(m - answer_midi) <= 12
            ]
            if not others:
                second, label = first, '같음'
            else:
                second, label = midi_to_note(self.rng.choice(others)), '다름'
        return [first, second], label

    def _build_choices(self, answer_midi, pool, octaves,
                       num_choices, distractor_strategy, proximity_strategy):
        answer_name = midi_to_note(answer_midi)[:-1]
        all_midi    = pool_to_midi_range(pool, octaves)
        candidates  = [
            m for m in all_midi
            if midi_to_note(m)[:-1] != answer_name
        ]
        if len(pool) <= 2 or distractor_strategy == 'use_all':
            distractor_pool = candidates
        else:
            distractor_pool = self._sort_by_proximity(answer_midi, candidates, proximity_strategy)

        distractors = self._pick_unique_name(distractor_pool, num_choices - 1)
        choices = [midi_to_note(answer_midi)] + [midi_to_note(d) for d in distractors]
        self.rng.shuffle(choices)
        return choices

    def _sort_by_proximity(self, answer_midi, candidates, strategy):
        if strategy == 'asc_by_distance':
            return sorted(candidates, key=lambda m: semitone_distance(m, answer_midi))
        elif strategy == 'desc_by_distance':
            return sorted(candidates, key=lambda m: semitone_distance(m, answer_midi), reverse=True)
        else:
            pool = candidates[:]
            self.rng.shuffle(pool)
            return pool

    def _pick_unique_name(self, candidates, n):
        seen, result = set(), []
        for m in candidates:
            name = midi_to_note(m)[:-1]
            if name not in seen:
                seen.add(name)
                result.append(m)
            if len(result) == n:
                break
        return result


# ══════════════════════════════════════════════════════════════════════════════
# 6. IntervalGenerator
# ══════════════════════════════════════════════════════════════════════════════
class IntervalGenerator:
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self._session_history: dict = {}

    def generate(self, step_id: str, difficulty_level: int) -> dict:
        step      = STEP_LOOKUP[step_id]
        at_rule   = self._get_answer_rule(step['answer_type'])
        d_rule    = self._get_difficulty_rule(difficulty_level)
        direction = step['direction']
        ipool     = parse_interval_pool(step['note_pool'])

        root_midi, symbol = self._pick_root_and_interval(
            step_id, ipool, d_rule['octaves'], direction
        )
        root_note  = midi_to_note(root_midi)
        upper_midi = build_interval_midi(root_midi, symbol, direction)
        upper_note = midi_to_note(upper_midi)
        answer_type = step['answer_type']

        if answer_type == 'same_diff':
            # present_notes: 제시된 두 음정 쌍(4음) / answer: '같음'/'다름' / choices: ['같음','다름']
            present_notes, same_diff_label = self._build_same_diff(
                root_midi, symbol, ipool, d_rule, direction
            )
            choices = ['같음', '다름']
        elif answer_type == 'height_compare':
            present_notes, choices = self._build_height_compare(
                root_midi, symbol, d_rule, direction
            )
            same_diff_label = None
        elif answer_type in ('interval_subj', 'keyboard_subj'):
            if direction == 'descending':
                present_notes = [upper_note, root_note]
            else:
                present_notes = [root_note, upper_note]
            choices = None
            same_diff_label = None
        else:  # name_2/3/4choice
            if direction == 'descending':
                present_notes = [upper_note, root_note]
            else:
                present_notes = [root_note, upper_note]
            choices = self._build_name_choices(
                symbol, ipool, at_rule['num_choices'], d_rule['proximity_strategy']
            )
            same_diff_label = None

        self._session_history.setdefault(step_id, []).append((root_midi, symbol))

        rec = {
            'step_id':            step_id,
            'step_name':          step['step_name'],
            'question_type':      'interval',
            'answer_type':        answer_type,
            'direction':          direction,
            'difficulty_level':   difficulty_level,
            'answer_interval':    symbol,
            'answer_interval_ko': interval_name_ko(symbol),
            'root_midi':          root_midi,
            'root_note':          root_note,
            'upper_midi':         upper_midi,
            'upper_note':         upper_note,
            'present_notes':      present_notes,
            'choices':            choices,
            'total_difficulty':   float(difficulty_level),
        }
        if same_diff_label is not None:
            rec['answer'] = same_diff_label
        return rec

    def reset_session(self):
        self._session_history = {}

    def _get_answer_rule(self, answer_type):
        keys = ['label', 'num_choices', 'present_count', 'distractor_strategy', 'pool_size_rule']
        return dict(zip(keys, ANSWER_TYPE_RULES[answer_type]))

    def _get_difficulty_rule(self, level):
        keys = ['label', 'octaves', 'proximity_strategy', 'proximity_semitones']
        return dict(zip(keys, DIFFICULTY_RULES[level]))

    def _pick_root_and_interval(self, step_id, ipool, octaves, direction):
        # rules.md 3-4: 같은 정답(음정 종류) 3회 연속 방지
        history = self._session_history.get(step_id, [])
        excluded_symbols = set()
        if len(history) >= 2 and history[-1][1] == history[-2][1]:
            excluded_symbols.add(history[-1][1])
        candidates = [
            (r, sym)
            for r in root_midi_pool(octaves)
            for sym in ipool
            if sym not in excluded_symbols
            and MIDI_MIN <= build_interval_midi(r, sym, direction) <= MIDI_MAX
        ]
        if not candidates:
            candidates = [
                (r, sym)
                for r in root_midi_pool(octaves)
                for sym in ipool
                if MIDI_MIN <= build_interval_midi(r, sym, direction) <= MIDI_MAX
            ]
        return self.rng.choice(candidates)

    def _build_same_diff(self, root_midi, symbol, ipool, d_rule, direction):
        # 두 음정은 항상 동일한 기준음(첫음)에서 출발한다.
        # height_compare 와의 차이: same_diff = 같은 출발음, 음정 종류가 같은지 판별
        is_same = self.rng.choice([True, False])
        p1_low, p1_high = interval_to_midi_pair(root_midi, symbol, direction)
        if is_same:
            label = '같음'
            p2_low, p2_high = p1_low, p1_high
        else:
            # 같은 기준음, 다른 음정 종류
            valid_others = [
                s for s in ipool if s != symbol
                and MIDI_MIN <= build_interval_midi(root_midi, s, direction) <= MIDI_MAX
            ]
            if not valid_others:
                label = '같음'
                p2_low, p2_high = p1_low, p1_high
            else:
                alt = self.rng.choice(valid_others)
                p2_low, p2_high = interval_to_midi_pair(root_midi, alt, direction)
                label = '다름'
        present = [midi_to_note(p1_low), midi_to_note(p1_high),
                   midi_to_note(p2_low), midi_to_note(p2_high)]
        return present, label

    def _build_height_compare(self, root_midi, symbol, d_rule, direction):
        alt_roots = [
            r for r in root_midi_pool(d_rule['octaves'])
            if MIDI_MIN <= build_interval_midi(r, symbol, direction) <= MIDI_MAX
            and r != root_midi
        ]
        alt_root = self.rng.choice(alt_roots) if alt_roots else root_midi
        p1_low, p1_high = interval_to_midi_pair(root_midi, symbol, direction)
        p2_low, p2_high = interval_to_midi_pair(alt_root,  symbol, direction)
        present = [midi_to_note(p1_low), midi_to_note(p1_high),
                   midi_to_note(p2_low), midi_to_note(p2_high)]
        return present, ['같음']

    def _build_name_choices(self, symbol, ipool, num_choices, proximity_strategy):
        target_st = interval_semitones(symbol)
        pool_syms = [s for s in ipool if s != symbol]
        if proximity_strategy == 'asc_by_distance':
            pool_syms.sort(key=lambda s: abs(interval_semitones(s) - target_st))
        elif proximity_strategy == 'desc_by_distance':
            pool_syms.sort(key=lambda s: abs(interval_semitones(s) - target_st), reverse=True)
        else:
            self.rng.shuffle(pool_syms)
        distractors = pool_syms[:num_choices - 1]
        choices = [interval_name_ko(symbol)] + [interval_name_ko(s) for s in distractors]
        self.rng.shuffle(choices)
        return choices


# ══════════════════════════════════════════════════════════════════════════════
# 7. 난이도 곡선 함수
# ══════════════════════════════════════════════════════════════════════════════
def difficulty_curve(n_questions: int, mode: str = 'linear',
                     fixed_level: int = 1,
                     custom_levels: Optional[list] = None) -> list:
    if mode == 'fixed':
        return [fixed_level] * n_questions
    elif mode == 'linear':
        return [min(1 + math.floor(i / n_questions * 3), 3) for i in range(n_questions)]
    elif mode == 'stairs':
        n1 = round(n_questions * 0.4)
        n3 = round(n_questions * 0.3)
        return [1] * n1 + [2] * (n_questions - n1 - n3) + [3] * n3
    elif mode == 'custom':
        if custom_levels is None or len(custom_levels) != n_questions:
            raise ValueError('custom_levels 길이가 n_questions와 다릅니다.')
        return custom_levels
    else:
        raise ValueError(f"mode='{mode}' 은 fixed|linear|stairs|custom 중 하나여야 합니다.")


# ══════════════════════════════════════════════════════════════════════════════
# 8. 범위 → step_id 목록 변환
# ══════════════════════════════════════════════════════════════════════════════
VALID_CATEGORY_PREFIXES = ('CAT_SN', 'CAT_INT')


def resolve_range(range_str: str) -> list:
    """
    범위 문자열 → 매칭되는 step_id 리스트

    예:
      'CAT_SN'              → 단일음 전체 step_id
      'CAT_SN_SC01'         → 7음계 코스 전체
      'CAT_SN_SC01_P01'     → P01 파트 전체
      'CAT_SN_SC01_P01_S01' → 특정 스텝 1개
    """
    # 최상위 카테고리로 시작해야 함
    if not any(range_str.startswith(p) for p in VALID_CATEGORY_PREFIXES):
        raise ValueError(
            f"범위 '{range_str}'는 CAT_SN 또는 CAT_INT 로 시작해야 합니다.\n"
            f"  불가능 예시: SC01_P01, P01_S01 (최상단 카테고리가 없으면 안됨)"
        )

    # 정확한 step_id 매칭
    if range_str in STEP_LOOKUP:
        return [range_str]

    # 접두사로 필터
    prefix = range_str if range_str.endswith('_') else range_str + '_'
    matched = [sid for sid in ALL_STEP_IDS if sid.startswith(prefix)]

    if not matched:
        raise ValueError(
            f"범위 '{range_str}'에 해당하는 스텝이 없습니다.\n"
            f"  사용 가능한 카테고리: {', '.join(c[0] for c in CATEGORY_DATA)}"
        )
    return matched


# ══════════════════════════════════════════════════════════════════════════════
# 9. 문제 배치 생성
# ══════════════════════════════════════════════════════════════════════════════
def generate_batch(step_ids: list, amount: int, diff_mode: str,
                   fixed_level: int, seed: Optional[int]) -> list:
    """
    step_ids 범위에서 amount 개 문제 생성 (step_id 랜덤 선택)
    """
    rng = random.Random(seed)
    levels = difficulty_curve(amount, mode=diff_mode, fixed_level=fixed_level)

    sn_gen  = SingleNoteGenerator(seed=seed)
    int_gen = IntervalGenerator(seed=seed)

    records = []
    for i, level in enumerate(levels, 1):
        sid  = rng.choice(step_ids)
        step = STEP_LOOKUP[sid]
        qtype = step['question_type']
        try:
            if qtype == 'single_note':
                q = sn_gen.generate(sid, level)
            else:
                q = int_gen.generate(sid, level)
            q['q_num'] = i
            records.append(q)
        except Exception as e:
            print(f'  [경고] {sid} 생성 실패: {e}', file=sys.stderr)

    return records


# ══════════════════════════════════════════════════════════════════════════════
# 9-b. 전체 경우 생성 (--all)
# ══════════════════════════════════════════════════════════════════════════════
def generate_all_exhaustive(step_ids: list, seed: Optional[int] = None) -> list:
    """
    step_ids 범위 내 등장 가능한 모든 문제를 빠짐없이 생성.

    - single_note: 난이도 옥타브 범위 내 모든 MIDI 음을 answer로 순회
      - same_diff → 음마다 '같음' / '다름' 2가지 생성
      - piano_subj → 음마다 1문제
      - name_Xchoice → 음마다 1문제 (distractors 결정론적 선택)
    - interval: 유효한 모든 (root_midi, symbol) 쌍을 순회
      - same_diff → 쌍마다 '같음' / '다름' 2가지 생성
      - height_compare → 쌍마다 1문제 (다른 높이 1개)
      - interval_subj / keyboard_subj → 쌍마다 1문제
      - name_Xchoice → 쌍마다 1문제
    """
    rng     = random.Random(seed)
    records = []

    # 전체 경우: 난이도 무관하게 C3~C6 전체 옥타브 사용 (rules.md 1-1)
    FULL_OCTAVES = [3, 4, 5, 6]

    for sid in step_ids:
        step         = STEP_LOOKUP[sid]
        diff_level   = step['difficulty_level']
        prox_strategy = DIFFICULTY_RULES[diff_level][2]   # octaves 다음 인덱스
        answer_type  = step['answer_type']
        at_vals      = ANSWER_TYPE_RULES[answer_type]
        num_choices  = at_vals[1]
        dist_strategy = at_vals[3]

        base = {
            'step_id':          sid,
            'step_name':        step['step_name'],
            'difficulty_level': diff_level,
            'total_difficulty': float(diff_level),
        }

        if step['question_type'] == 'single_note':
            pool      = parse_pool(step['note_pool'])
            midi_pool = pool_to_midi_range(pool, FULL_OCTAVES)

            for answer_midi in midi_pool:
                answer      = midi_to_note(answer_midi)
                answer_name = answer[:-1]

                if answer_type == 'same_diff':
                    # 같음: answer='같음', choices=['같음','다름'], present=[음,음]
                    records.append({**base,
                        'question_type': 'single_note', 'answer_type': answer_type,
                        'direction': '-', 'answer': '같음', 'answer_midi': answer_midi,
                        'present_notes': [answer, answer], 'choices': ['같음', '다름'],
                    })
                    # 다름: 다른 음이름 & 첫 번째 음 기준 1옥타브 이내 모든 조합
                    all_second = pool_to_midi_range(pool, FULL_OCTAVES)
                    for second_midi in all_second:
                        if midi_to_note(second_midi)[:-1] != answer_name and abs(second_midi - answer_midi) <= 12:
                            records.append({**base,
                                'question_type': 'single_note', 'answer_type': answer_type,
                                'direction': '-', 'answer': '다름', 'answer_midi': answer_midi,
                                'present_notes': [answer, midi_to_note(second_midi)],
                                'choices': ['같음', '다름'],
                            })

                elif answer_type == 'piano_subj':
                    records.append({**base,
                        'question_type': 'single_note', 'answer_type': answer_type,
                        'direction': '-', 'answer': answer, 'answer_midi': answer_midi,
                        'present_notes': [answer], 'choices': None,
                    })

                else:  # name_2/3/4choice — 오답은 풀 내부에서만 (rules.md 3-1)
                    candidates = [
                        m for m in midi_pool
                        if midi_to_note(m)[:-1] != answer_name
                    ]
                    if len(pool) <= 2 or dist_strategy == 'use_all':
                        distractor_pool = candidates
                    elif prox_strategy == 'asc_by_distance':
                        distractor_pool = sorted(candidates,
                                                 key=lambda m: semitone_distance(m, answer_midi))
                    elif prox_strategy == 'desc_by_distance':
                        distractor_pool = sorted(candidates,
                                                 key=lambda m: semitone_distance(m, answer_midi),
                                                 reverse=True)
                    else:
                        distractor_pool = candidates[:]
                        rng.shuffle(distractor_pool)

                    seen, distractors = set(), []
                    for m in distractor_pool:
                        nm = midi_to_note(m)[:-1]
                        if nm not in seen:
                            seen.add(nm)
                            distractors.append(m)
                        if len(distractors) == num_choices - 1:
                            break
                    choices = [answer] + [midi_to_note(d) for d in distractors]
                    rng.shuffle(choices)
                    records.append({**base,
                        'question_type': 'single_note', 'answer_type': answer_type,
                        'direction': '-', 'answer': answer, 'answer_midi': answer_midi,
                        'present_notes': [answer], 'choices': choices,
                    })

        else:  # interval
            ipool     = parse_interval_pool(step['note_pool'])
            direction = step['direction']
            # 난이도 무관: C3~C6 전체에서 유효한 모든 (기준음, 음정) 쌍 열거
            all_pairs = [
                (r, sym)
                for r in root_midi_pool(FULL_OCTAVES)
                for sym in ipool
                if MIDI_MIN <= build_interval_midi(r, sym, direction) <= MIDI_MAX
            ]

            for root_midi, symbol in all_pairs:
                root_note    = midi_to_note(root_midi)
                upper_midi   = build_interval_midi(root_midi, symbol, direction)
                upper_note   = midi_to_note(upper_midi)
                present_base = ([upper_note, root_note] if direction == 'descending'
                                else [root_note, upper_note])
                int_base = {**base,
                    'question_type':      'interval',
                    'answer_type':        answer_type,
                    'direction':          direction,
                    'answer_interval':    symbol,
                    'answer_interval_ko': interval_name_ko(symbol),
                    'root_midi':          root_midi,
                    'root_note':          root_note,
                    'upper_midi':         upper_midi,
                    'upper_note':         upper_note,
                }

                if answer_type == 'same_diff':
                    # 같음: answer='같음', choices=['같음','다름'], 같은 음정 쌍 두 번 제시
                    p1l, p1h = interval_to_midi_pair(root_midi, symbol, direction)
                    records.append({**int_base,
                        'answer': '같음',
                        'present_notes': [midi_to_note(p1l), midi_to_note(p1h),
                                          midi_to_note(p1l), midi_to_note(p1h)],
                        'choices': ['같음', '다름'],
                    })
                    # 다름: 같은 기준음, 다른 음정 종류 (첫음이 동일해야 함)
                    for alt in [s for s in ipool if s != symbol]:
                        if MIDI_MIN <= build_interval_midi(root_midi, alt, direction) <= MIDI_MAX:
                            p2l, p2h = interval_to_midi_pair(root_midi, alt, direction)
                            records.append({**int_base,
                                'answer': '다름',
                                'present_notes': [midi_to_note(p1l), midi_to_note(p1h),
                                                  midi_to_note(p2l), midi_to_note(p2h)],
                                'choices': ['같음', '다름'],
                            })

                elif answer_type == 'height_compare':
                    # 같은 음정을 다른 높이에서 제시 — 모든 유효 alt_root와 조합
                    p1l, p1h = interval_to_midi_pair(root_midi, symbol, direction)
                    alt_roots = sorted(
                        r for r in root_midi_pool(FULL_OCTAVES)
                        if MIDI_MIN <= build_interval_midi(r, symbol, direction) <= MIDI_MAX
                        and r != root_midi
                    )
                    for alt_root in alt_roots:
                        p2l, p2h = interval_to_midi_pair(alt_root, symbol, direction)
                        records.append({**int_base,
                            'present_notes': [midi_to_note(p1l), midi_to_note(p1h),
                                              midi_to_note(p2l), midi_to_note(p2h)],
                            'choices': ['같음'],
                        })

                elif answer_type in ('interval_subj', 'keyboard_subj'):
                    records.append({**int_base,
                        'present_notes': present_base, 'choices': None,
                    })

                else:  # name_2/3/4choice — 오답은 풀 내부에서만 (rules.md 3-1)
                    target_st = interval_semitones(symbol)
                    pool_syms = [s for s in ipool if s != symbol]
                    if prox_strategy == 'asc_by_distance':
                        pool_syms.sort(key=lambda s: abs(interval_semitones(s) - target_st))
                    elif prox_strategy == 'desc_by_distance':
                        pool_syms.sort(key=lambda s: abs(interval_semitones(s) - target_st),
                                       reverse=True)
                    else:
                        rng.shuffle(pool_syms)
                    distractors = pool_syms[:num_choices - 1]
                    choices = [interval_name_ko(symbol)] + [interval_name_ko(s) for s in distractors]
                    rng.shuffle(choices)
                    records.append({**int_base,
                        'present_notes': present_base, 'choices': choices,
                    })

    return records


# ══════════════════════════════════════════════════════════════════════════════
# 10. 레코드 → 출력용 행 변환
# ══════════════════════════════════════════════════════════════════════════════
def record_to_row(q: dict, range_label: str) -> dict:
    """문제 dict → 출력 테이블 행 dict"""
    direction  = q.get('direction', '-')
    sep = ' + ' if direction == 'harmonic' else ' → '
    present_str = sep.join(q['present_notes'])

    if q.get('answer_type') == 'same_diff':
        answer_str = q.get('answer', '?')   # '같음' 또는 '다름'
    elif q['question_type'] == 'interval':
        answer_str = f"{q['answer_interval']} ({q['answer_interval_ko']})"
    else:
        answer_str = q['answer']

    choices = q.get('choices')
    choices_str = ', '.join(choices) if choices else '(주관식)'
    diff_label  = f"Lv.{q['difficulty_level']} ({DIFFICULTY_RULES[q['difficulty_level']][0]})"

    return {
        '#':             q['q_num'],
        'range':         range_label,
        'step_id':       q['step_id'],
        'step_name':     q['step_name'],
        'question_type': q['question_type'],
        'answer_type':   q['answer_type'],
        'direction':     direction,
        'difficulty':    diff_label,
        'present':       present_str,
        'answer':        answer_str,
        'choices':       choices_str,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 11. 출력 포맷터
# ══════════════════════════════════════════════════════════════════════════════
def output_print(rows: list):
    if not rows:
        print('생성된 문제가 없습니다.')
        return
    col_widths = {k: len(k) for k in rows[0]}
    for row in rows:
        for k, v in row.items():
            col_widths[k] = max(col_widths[k], len(str(v)))

    header = '  '.join(k.ljust(col_widths[k]) for k in rows[0])
    sep    = '  '.join('-' * col_widths[k] for k in rows[0])
    print(header)
    print(sep)
    for row in rows:
        print('  '.join(str(row[k]).ljust(col_widths[k]) for k in row))


def output_csv(rows: list, filepath: str):
    import csv
    os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f'CSV 저장: {filepath}')


def output_xlsx(rows: list, filepath: str):
    if not HAS_PANDAS or not HAS_OPENPYXL:
        missing = []
        if not HAS_PANDAS:    missing.append('pandas')
        if not HAS_OPENPYXL:  missing.append('openpyxl')
        print(f'[오류] xlsx 출력에는 {", ".join(missing)} 가 필요합니다.')
        print(f'       pip install {" ".join(missing)}')
        return
    os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_excel(filepath, index=False, engine='openpyxl')
    print(f'XLSX 저장: {filepath}')


def output_md(rows: list, filepath: str):
    os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
    if not rows:
        return
    keys = list(rows[0].keys())
    lines = []
    lines.append('| ' + ' | '.join(keys) + ' |')
    lines.append('| ' + ' | '.join('---' for _ in keys) + ' |')
    for row in rows:
        lines.append('| ' + ' | '.join(str(row[k]) for k in keys) + ' |')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'MD 저장: {filepath}')


# ══════════════════════════════════════════════════════════════════════════════
# 12. CLI
# ══════════════════════════════════════════════════════════════════════════════
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='eargenx',
        description='청음 문제 더미데이터 생성기',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python eargenx.py
  python eargenx.py --range CAT_SN_SC01 --amount 20
  python eargenx.py -r CAT_SN CAT_INT -a 10 -f xlsx csv -o output/
  python eargenx.py -r CAT_INT_SC06_P04_S03 CAT_INT_SC06_P04_S04 -a 5
  python eargenx.py -r CAT_INT_SC01_P01 --difficulty stairs --shuffle
  python eargenx.py -r CAT_SN_SC01_P03_S04 -a 5 --seed 42 -f print xlsx

범위 형식 (반드시 CAT_SN 또는 CAT_INT 로 시작):
  CAT_SN                    단일음 전체
  CAT_SN_SC01               7음계 코스 전체
  CAT_SN_SC01_P01           파트 전체
  CAT_SN_SC01_P01_S01       특정 스텝
  CAT_INT                   음정 전체
  CAT_INT_SC02_P03          SC02 P03 파트 전체

범위 지정 방식:
  -r A B C          한 플래그에 공백으로 여러 범위 지정
  -r A -r B -r C    플래그 반복으로 여러 범위 지정 (동일 결과)

범위 코드
  CAT: 카테고리 | SC: 코스 | P: 파트 | S: 스텝
  SN: 단일 음 | INT: 음정 |
        """,
    )
    parser.add_argument(
        '--range', '--r', '-r',
        dest='ranges', metavar='RANGE', nargs='+', action='extend',
        help='문제 범위 (띄어쓰기 또는 반복 사용 가능). 예: -r CAT_SN_SC01_P01 CAT_INT_SC06_P04_S03'
    )
    parser.add_argument(
        '--seed', '--sd',
        dest='seed', type=int, default=None, metavar='N',
        help='랜덤 시드 (미입력 시 랜덤)'
    )
    parser.add_argument(
        '--amount', '-a',
        dest='amount', type=int, default=10, metavar='N',
        help='범위당 문제 개수 (기본값: 10)'
    )
    parser.add_argument(
        '--difficulty', '-d',
        dest='difficulty', default='linear', metavar='MODE',
        help='난이도 설정: 1, 2, 3 (고정) 또는 linear, stairs, fixed (곡선). 기본값: linear'
    )
    parser.add_argument(
        '--shuffle', '-s',
        dest='shuffle', action='store_true',
        help='전체 문제 셔플'
    )
    parser.add_argument(
        '--format', '-f',
        dest='formats', metavar='FMT', nargs='+',
        choices=['xlsx', 'csv', 'md', 'print'],
        default=['print'],
        help='출력 포맷 (복수 선택 가능): xlsx, csv, md, print. 기본값: print'
    )
    parser.add_argument(
        '--output', '-o',
        dest='output', default='example/', metavar='PATH',
        help='저장 경로 (기본값: example/)'
    )
    parser.add_argument(
        '--all', '-A',
        dest='all_questions', action='store_true',
        help='범위 내 등장 가능한 모든 문제 생성 (--amount 무시)'
    )
    return parser


def parse_difficulty(diff_str: str) -> tuple:
    """'1'|'2'|'3' → (fixed, level), 'linear'|'stairs' → (mode, 1)"""
    if diff_str in ('1', '2', '3'):
        return 'fixed', int(diff_str)
    elif diff_str in ('linear', 'stairs', 'fixed', 'custom'):
        return diff_str, 1
    else:
        raise ValueError(
            f"--difficulty '{diff_str}' 은 1, 2, 3 또는 linear, stairs, fixed 중 하나여야 합니다."
        )


def make_filepath(output_dir: str, fmt: str, timestamp: str) -> str:
    filename = f'eartraining_{timestamp}.{fmt}'
    return os.path.join(output_dir, filename)


# ══════════════════════════════════════════════════════════════════════════════
# 13. 메인
# ══════════════════════════════════════════════════════════════════════════════
def main():
    parser = build_parser()
    args   = parser.parse_args()

    # ── 범위 결정 ────────────────────────────────────────────────────────────
    if not args.ranges:
        # 기본값: 랜덤 스텝 1개
        rng = random.Random(args.seed)
        random_step = rng.choice(ALL_STEP_IDS)
        print(f'[기본값] 랜덤 스텝 선택: {random_step}')
        ranges = [('random', [random_step])]
    else:
        ranges = []
        for r in args.ranges:
            try:
                step_ids = resolve_range(r)
                ranges.append((r, step_ids))
                print(f'[범위] {r} → {len(step_ids)}개 스텝 매칭')
            except ValueError as e:
                print(f'[오류] {e}', file=sys.stderr)
                sys.exit(1)

    # ── 난이도 파싱 ──────────────────────────────────────────────────────────
    try:
        diff_mode, fixed_level = parse_difficulty(args.difficulty)
    except ValueError as e:
        print(f'[오류] {e}', file=sys.stderr)
        sys.exit(1)

    # ── 문제 생성 ────────────────────────────────────────────────────────────
    all_rows = []
    q_counter = 0
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    for range_label, step_ids in ranges:
        if args.all_questions:
            print(f'\n생성 중: [{range_label}] 전체 경우 (--all) ...')
            batch = generate_all_exhaustive(step_ids=step_ids, seed=args.seed)
            print(f'  → {len(batch)}개 문제 산출')
        else:
            print(f'\n생성 중: [{range_label}] {args.amount}문제 ...')
            batch = generate_batch(
                step_ids=step_ids,
                amount=args.amount,
                diff_mode=diff_mode,
                fixed_level=fixed_level,
                seed=args.seed,
            )
        for q in batch:
            q_counter += 1
            q['q_num'] = q_counter
            all_rows.append(record_to_row(q, range_label))

    if not all_rows:
        print('[오류] 생성된 문제가 없습니다.', file=sys.stderr)
        sys.exit(1)

    # ── 셔플 ─────────────────────────────────────────────────────────────────
    if args.shuffle:
        rng = random.Random(args.seed)
        rng.shuffle(all_rows)
        for i, row in enumerate(all_rows, 1):
            row['#'] = i

    # ── 출력 ─────────────────────────────────────────────────────────────────
    print(f'\n총 {len(all_rows)}개 문제 생성 완료.\n')

    for fmt in args.formats:
        if fmt == 'print':
            output_print(all_rows)
        elif fmt == 'csv':
            fp = make_filepath(args.output, 'csv', timestamp)
            output_csv(all_rows, fp)
        elif fmt == 'xlsx':
            fp = make_filepath(args.output, 'xlsx', timestamp)
            output_xlsx(all_rows, fp)
        elif fmt == 'md':
            fp = make_filepath(args.output, 'md', timestamp)
            output_md(all_rows, fp)


if __name__ == '__main__':
    main()
