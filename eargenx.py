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
from typing import Optional

from config import MIDI_MIN, MIDI_MAX, DEFAULT_AMOUNT, DEFAULT_OUTPUT, DEFAULT_DIFFICULTY, DEFAULT_FORMATS
from curriculum import (
    NOTE_NAMES, ENHARMONIC_MAP, INTERVAL_SEMITONES,
    ANSWER_TYPE_RULES, DIFFICULTY_RULES,
    CATEGORY_DATA, STEP_LOOKUP, ALL_STEP_IDS,
    INT_REVIEW_EXPANSION, VALID_CATEGORY_PREFIXES,
)

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
# 1. 음 유틸 (MIDI ↔ 음이름 변환)
# ══════════════════════════════════════════════════════════════════════════════
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


def octave_difficulty(ref_midi: int) -> float:
    """C4(MIDI 60) 기준 옥타브 거리로 total_difficulty 계산 (1.0 ~ 3.0)"""
    return 1.0 + abs(ref_midi // 12 - 60 // 12)


# ══════════════════════════════════════════════════════════════════════════════
# 2. SingleNoteGenerator
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
            'total_difficulty': octave_difficulty(answer_midi),
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
        candidates  = [m for m in all_midi if midi_to_note(m)[:-1] != answer_name]
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


# ──────────────────────────────────────────────────────────────────────────────
# IntervalGenerator 케이스 열거 헬퍼
# 랜덤 생성(IntervalGenerator)과 전체 열거(generate_all_exhaustive) 양쪽에서 공유.
# 규칙 변경 시 이 함수만 수정하면 됩니다.
# ──────────────────────────────────────────────────────────────────────────────

def _same_diff_cases(symbol: str, ipool: list, direction: str) -> list:
    """5-3 같음/다름: 루트를 C4(60)으로 고정하고 가능한 모든 (present_notes, label) 반환."""
    root = 60  # 항상 C4
    p1l, p1h = interval_to_midi_pair(root, symbol, direction)
    p1_notes = [midi_to_note(p1l), midi_to_note(p1h)]
    cases = [(p1_notes + p1_notes, '같음')]
    for alt in ipool:
        if alt != symbol and MIDI_MIN <= build_interval_midi(root, alt, direction) <= MIDI_MAX:
            p2l, p2h = interval_to_midi_pair(root, alt, direction)
            cases.append((p1_notes + [midi_to_note(p2l), midi_to_note(p2h)], '다름'))
    return cases


def _height_compare_cases(root_midi: int, symbol: str, ipool: list, direction: str) -> list:
    """5-4 다양한 높이 비교: root_fixed/top_fixed 모든 (present_notes, label) 반환."""
    p1l, p1h = interval_to_midi_pair(root_midi, symbol, direction)
    p1_notes = [midi_to_note(p1l), midi_to_note(p1h)]
    top_midi = p1h  # 높은 음 (ascending: root+st, descending: root)

    cases = [(p1_notes + p1_notes, '같음')]  # root_fixed/top_fixed 같음 (동일)

    # root_fixed 다름: 같은 루트, 다른 심볼
    for alt in ipool:
        if alt != symbol and MIDI_MIN <= build_interval_midi(root_midi, alt, direction) <= MIDI_MAX:
            p2l, p2h = interval_to_midi_pair(root_midi, alt, direction)
            cases.append((p1_notes + [midi_to_note(p2l), midi_to_note(p2h)], '다름'))

    # top_fixed 다름: 같은 상단음, 다른 심볼 (루트가 달라짐)
    for alt in ipool:
        if alt != symbol:
            if direction == 'ascending':
                alt_root = top_midi - interval_semitones(alt)
            else:  # descending: 루트가 곧 상단음
                alt_root = top_midi
            if MIDI_MIN <= alt_root <= MIDI_MAX and alt_root != root_midi:
                p2l, p2h = interval_to_midi_pair(alt_root, alt, direction)
                cases.append((p1_notes + [midi_to_note(p2l), midi_to_note(p2h)], '다름'))

    return cases


# ══════════════════════════════════════════════════════════════════════════════
# 3. IntervalGenerator
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
            present_notes, same_diff_label = self._build_same_diff(
                root_midi, symbol, ipool, d_rule, direction
            )
            choices = ['같음', '다름']
        elif answer_type == 'height_compare':
            present_notes, same_diff_label = self._build_height_compare(
                root_midi, symbol, ipool, d_rule, direction
            )
            choices = ['같음', '다름']
        elif answer_type in ('interval_subj', 'keyboard_subj'):
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
            'total_difficulty':   octave_difficulty(root_midi),
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
        present, label = self.rng.choice(_same_diff_cases(symbol, ipool, direction))
        return present, label

    def _build_height_compare(self, root_midi, symbol, ipool, d_rule, direction):
        present, label = self.rng.choice(_height_compare_cases(root_midi, symbol, ipool, direction))
        return present, label

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
# 4. 난이도 곡선 함수
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
# 5. 범위 → step_id 목록 변환
# ══════════════════════════════════════════════════════════════════════════════
def resolve_range(range_str: str) -> list:
    if not any(range_str.startswith(p) for p in VALID_CATEGORY_PREFIXES):
        raise ValueError(
            f"범위 '{range_str}'는 CAT_SN 또는 CAT_INT 로 시작해야 합니다.\n"
            f"  불가능 예시: SC01_P01, P01_S01 (최상단 카테고리가 없으면 안됨)"
        )

    if range_str in STEP_LOOKUP:
        return [range_str]

    if range_str in INT_REVIEW_EXPANSION:
        return INT_REVIEW_EXPANSION[range_str]

    prefix = range_str if range_str.endswith('_') else range_str + '_'
    matched = [sid for sid in ALL_STEP_IDS if sid.startswith(prefix)]

    if not matched:
        raise ValueError(
            f"범위 '{range_str}'에 해당하는 스텝이 없습니다.\n"
            f"  사용 가능한 카테고리: {', '.join(c[0] for c in CATEGORY_DATA)}"
        )
    return matched


# ══════════════════════════════════════════════════════════════════════════════
# 6. 문제 배치 생성
# ══════════════════════════════════════════════════════════════════════════════
def generate_batch(step_ids: list, amount: int, diff_mode: str,
                   fixed_level: int, seed: Optional[int]) -> list:
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


def generate_all_exhaustive(step_ids: list, seed: Optional[int] = None) -> list:
    rng     = random.Random(seed)
    records = []
    FULL_OCTAVES = [3, 4, 5, 6]

    for sid in step_ids:
        step         = STEP_LOOKUP[sid]
        diff_level   = step['difficulty_level']
        prox_strategy = DIFFICULTY_RULES[diff_level][2]
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
                    records.append({**base,
                        'question_type': 'single_note', 'answer_type': answer_type,
                        'direction': '-', 'answer': '같음', 'answer_midi': answer_midi,
                        'present_notes': [answer, answer], 'choices': ['같음', '다름'],
                        'total_difficulty': octave_difficulty(answer_midi),
                    })
                    all_second = pool_to_midi_range(pool, FULL_OCTAVES)
                    for second_midi in all_second:
                        if midi_to_note(second_midi)[:-1] != answer_name and abs(second_midi - answer_midi) <= 12:
                            records.append({**base,
                                'question_type': 'single_note', 'answer_type': answer_type,
                                'direction': '-', 'answer': '다름', 'answer_midi': answer_midi,
                                'present_notes': [answer, midi_to_note(second_midi)],
                                'choices': ['같음', '다름'],
                                'total_difficulty': octave_difficulty(answer_midi),
                            })

                elif answer_type == 'piano_subj':
                    records.append({**base,
                        'question_type': 'single_note', 'answer_type': answer_type,
                        'direction': '-', 'answer': answer, 'answer_midi': answer_midi,
                        'present_notes': [answer], 'choices': None,
                        'total_difficulty': octave_difficulty(answer_midi),
                    })

                else:
                    candidates = [m for m in midi_pool if midi_to_note(m)[:-1] != answer_name]
                    if len(pool) <= 2 or dist_strategy == 'use_all':
                        distractor_pool = candidates
                    elif prox_strategy == 'asc_by_distance':
                        distractor_pool = sorted(candidates, key=lambda m: semitone_distance(m, answer_midi))
                    elif prox_strategy == 'desc_by_distance':
                        distractor_pool = sorted(candidates, key=lambda m: semitone_distance(m, answer_midi), reverse=True)
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
                        'total_difficulty': octave_difficulty(answer_midi),
                    })

        else:  # interval
            ipool     = parse_interval_pool(step['note_pool'])
            direction = step['direction']
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
                present_base = [root_note, upper_note]
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
                    'total_difficulty':   octave_difficulty(root_midi),
                }

                if answer_type == 'same_diff':
                    # 5-3 규칙: C4 기준으로 생성 — root_midi가 60일 때만 처리해 중복 방지
                    if root_midi != 60:
                        continue
                    for present_notes, answer in _same_diff_cases(symbol, ipool, direction):
                        records.append({**int_base,
                            'answer': answer, 'present_notes': present_notes,
                            'choices': ['같음', '다름'],
                        })

                elif answer_type == 'height_compare':
                    for present_notes, answer in _height_compare_cases(root_midi, symbol, ipool, direction):
                        records.append({**int_base,
                            'answer': answer, 'present_notes': present_notes,
                            'choices': ['같음', '다름'],
                        })

                elif answer_type in ('interval_subj', 'keyboard_subj'):
                    records.append({**int_base,
                        'present_notes': present_base, 'choices': None,
                    })

                else:  # name_2/3/4choice
                    target_st = interval_semitones(symbol)
                    pool_syms = [s for s in ipool if s != symbol]
                    if prox_strategy == 'asc_by_distance':
                        pool_syms.sort(key=lambda s: abs(interval_semitones(s) - target_st))
                    elif prox_strategy == 'desc_by_distance':
                        pool_syms.sort(key=lambda s: abs(interval_semitones(s) - target_st), reverse=True)
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
# 7. 레코드 → 출력용 행 변환
# ══════════════════════════════════════════════════════════════════════════════
def record_to_row(q: dict, range_label: str) -> dict:
    direction  = q.get('direction', '-')
    sep = ' + ' if direction == 'harmonic' else ' → '
    notes = q['present_notes']
    if len(notes) == 4:
        present_str = sep.join(notes[:2]) + ' | ' + sep.join(notes[2:])
    else:
        present_str = sep.join(notes)

    if q.get('answer_type') == 'keyboard_subj':
        given_note  = q['root_note'] if direction != 'descending' else q['upper_note']
        target_note = q['upper_note'] if direction != 'descending' else q['root_note']
        present_str = f"{given_note} | {q['answer_interval']} ({q['answer_interval_ko']})"
        answer_str  = target_note
    elif q.get('answer_type') == 'interval_subj':
        answer_str = present_str
    elif q.get('answer_type') in ('same_diff', 'height_compare'):
        answer_str = q.get('answer', '?')
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
# 8. 출력 포맷터
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
# 9. CLI
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
        dest='amount', type=int, default=DEFAULT_AMOUNT, metavar='N',
        help=f'범위당 문제 개수 (기본값: {DEFAULT_AMOUNT})'
    )
    parser.add_argument(
        '--difficulty', '-d',
        dest='difficulty', default=DEFAULT_DIFFICULTY, metavar='MODE',
        help=f'난이도 설정: 1, 2, 3 (고정) 또는 linear, stairs, fixed (곡선). 기본값: {DEFAULT_DIFFICULTY}'
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
        default=DEFAULT_FORMATS,
        help=f'출력 포맷 (복수 선택 가능): xlsx, csv, md, print. 기본값: {DEFAULT_FORMATS[0]}'
    )
    parser.add_argument(
        '--output', '-o',
        dest='output', default=DEFAULT_OUTPUT, metavar='PATH',
        help=f'저장 경로 (기본값: {DEFAULT_OUTPUT})'
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
# 10. 메인
# ══════════════════════════════════════════════════════════════════════════════
def main():
    parser = build_parser()
    args   = parser.parse_args()

    # ── 범위 결정 ────────────────────────────────────────────────────────────
    if not args.ranges:
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
