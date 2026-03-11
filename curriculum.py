# curriculum.py — EarGenX 커리큘럼 데이터 및 규칙 테이블

# ══════════════════════════════════════════════════════════════════════════════
# 음악 이론 상수
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

# ══════════════════════════════════════════════════════════════════════════════
# 정답 유형 및 난이도 규칙
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
    1: ('쉬움',   [4],            'desc_by_distance', '≥5반음/≥4반음차(오답 멀리)'),
    2: ('보통',   [3, 5],         'shuffle',           '무작위 배치'),
    3: ('어려움', [3, 4, 5, 6],   'asc_by_distance',  '≤2반음/≤1반음차(오답 가까이)'),
}

# ══════════════════════════════════════════════════════════════════════════════
# 커리큘럼 계층 데이터
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
    ('CAT_INT_SC02', 'CAT_INT_SC02_P04', '파트04 — 전체복습',              'P1,m2,M2,m3,M3'),
    ('CAT_INT_SC03', 'CAT_INT_SC03_P01', '파트01 — 장3도, 완전4도',        'M3,P4'),
    ('CAT_INT_SC03', 'CAT_INT_SC03_P02', '파트02 — 단3도, 장3도, 완전4도', 'm3,M3,P4'),
    ('CAT_INT_SC03', 'CAT_INT_SC03_P03', '파트03 — 완전4도, 증4도',        'P4,A4'),
    ('CAT_INT_SC03', 'CAT_INT_SC03_P04', '파트04 — 전체복습',              'P1,m2,M2,m3,M3,P4,A4'),
    ('CAT_INT_SC04', 'CAT_INT_SC04_P01', '파트01 — 완전4도, 완전5도',      'P4,P5'),
    ('CAT_INT_SC04', 'CAT_INT_SC04_P02', '파트02 — 증4도, 완전5도',        'A4,P5'),
    ('CAT_INT_SC04', 'CAT_INT_SC04_P03', '파트03 — 전체복습',              'P1,m2,M2,m3,M3,P4,A4,P5'),
    ('CAT_INT_SC05', 'CAT_INT_SC05_P01', '파트01 — 장3도, 단6도',          'M3,m6'),
    ('CAT_INT_SC05', 'CAT_INT_SC05_P02', '파트02 — 단3도, 장6도',          'm3,M6'),
    ('CAT_INT_SC05', 'CAT_INT_SC05_P03', '파트03 — 단6도, 장6도',          'm6,M6'),
    ('CAT_INT_SC05', 'CAT_INT_SC05_P04', '파트04 — 전체복습',              'P1,m2,M2,m3,M3,P4,A4,P5,m6,M6'),
    ('CAT_INT_SC06', 'CAT_INT_SC06_P01', '파트01 — 장2도, 단7도',          'M2,m7'),
    ('CAT_INT_SC06', 'CAT_INT_SC06_P02', '파트02 — 단2도, 장7도',          'm2,M7'),
    ('CAT_INT_SC06', 'CAT_INT_SC06_P03', '파트03 — 단7도, 장7도',          'm7,M7'),
    ('CAT_INT_SC06', 'CAT_INT_SC06_P04', '파트04 — 전체복습',              'P1,m2,M2,m3,M3,P4,A4,P5,m6,M6,m7,M7'),
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
    ('CAT_INT_SC02_P04', 'CAT_INT_SC02_P04_S01', '음정 이름 고르기',     'interval', 'P1,m2,M2,m3,M3', 'ascending',  'name_3choice',  2),
    ('CAT_INT_SC02_P04', 'CAT_INT_SC02_P04_S02', '상행 음정 알아맞히기', 'interval', 'P1,m2,M2,m3,M3', 'ascending',  'interval_subj', 2),
    ('CAT_INT_SC02_P04', 'CAT_INT_SC02_P04_S03', '하행 음정 알아맞히기', 'interval', 'P1,m2,M2,m3,M3', 'descending', 'interval_subj', 2),
    ('CAT_INT_SC02_P04', 'CAT_INT_SC02_P04_S04', '건반에서 음정 선택',   'interval', 'P1,m2,M2,m3,M3', 'ascending',  'keyboard_subj', 2),
    ('CAT_INT_SC02_P04', 'CAT_INT_SC02_P04_S05', '화음에서 음정 찾기',   'interval', 'P1,m2,M2,m3,M3', 'harmonic',   'interval_subj', 2),
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
    ('CAT_INT_SC03_P04', 'CAT_INT_SC03_P04_S01', '음정 이름 고르기',     'interval', 'P1,m2,M2,m3,M3,P4,A4', 'ascending',  'name_4choice',  2),
    ('CAT_INT_SC03_P04', 'CAT_INT_SC03_P04_S02', '상행 음정 알아맞히기', 'interval', 'P1,m2,M2,m3,M3,P4,A4', 'ascending',  'interval_subj', 2),
    ('CAT_INT_SC03_P04', 'CAT_INT_SC03_P04_S03', '하행 음정 알아맞히기', 'interval', 'P1,m2,M2,m3,M3,P4,A4', 'descending', 'interval_subj', 2),
    ('CAT_INT_SC03_P04', 'CAT_INT_SC03_P04_S04', '건반에서 음정 선택',   'interval', 'P1,m2,M2,m3,M3,P4,A4', 'ascending',  'keyboard_subj', 2),
    ('CAT_INT_SC03_P04', 'CAT_INT_SC03_P04_S05', '화음에서 음정 찾기',   'interval', 'P1,m2,M2,m3,M3,P4,A4', 'harmonic',   'interval_subj', 2),
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
    ('CAT_INT_SC04_P03', 'CAT_INT_SC04_P03_S01', '음정 이름 고르기',     'interval', 'P1,m2,M2,m3,M3,P4,A4,P5', 'ascending',  'name_3choice',  2),
    ('CAT_INT_SC04_P03', 'CAT_INT_SC04_P03_S02', '상행 음정 알아맞히기', 'interval', 'P1,m2,M2,m3,M3,P4,A4,P5', 'ascending',  'interval_subj', 2),
    ('CAT_INT_SC04_P03', 'CAT_INT_SC04_P03_S03', '하행 음정 알아맞히기', 'interval', 'P1,m2,M2,m3,M3,P4,A4,P5', 'descending', 'interval_subj', 2),
    ('CAT_INT_SC04_P03', 'CAT_INT_SC04_P03_S04', '건반에서 음정 선택',   'interval', 'P1,m2,M2,m3,M3,P4,A4,P5', 'ascending',  'keyboard_subj', 2),
    ('CAT_INT_SC04_P03', 'CAT_INT_SC04_P03_S05', '화음에서 음정 찾기',   'interval', 'P1,m2,M2,m3,M3,P4,A4,P5', 'harmonic',   'interval_subj', 2),
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
    ('CAT_INT_SC05_P04', 'CAT_INT_SC05_P04_S01', '음정 이름 고르기',     'interval', 'P1,m2,M2,m3,M3,P4,A4,P5,m6,M6', 'ascending',  'name_4choice',  3),
    ('CAT_INT_SC05_P04', 'CAT_INT_SC05_P04_S02', '상행 음정 알아맞히기', 'interval', 'P1,m2,M2,m3,M3,P4,A4,P5,m6,M6', 'ascending',  'interval_subj', 3),
    ('CAT_INT_SC05_P04', 'CAT_INT_SC05_P04_S03', '하행 음정 알아맞히기', 'interval', 'P1,m2,M2,m3,M3,P4,A4,P5,m6,M6', 'descending', 'interval_subj', 3),
    ('CAT_INT_SC05_P04', 'CAT_INT_SC05_P04_S04', '건반에서 음정 선택',   'interval', 'P1,m2,M2,m3,M3,P4,A4,P5,m6,M6', 'ascending',  'keyboard_subj', 3),
    ('CAT_INT_SC05_P04', 'CAT_INT_SC05_P04_S05', '화음에서 음정 찾기',   'interval', 'P1,m2,M2,m3,M3,P4,A4,P5,m6,M6', 'harmonic',   'interval_subj', 3),
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
    ('CAT_INT_SC06_P04', 'CAT_INT_SC06_P04_S01', '음정 이름 고르기',     'interval', 'P1,m2,M2,m3,M3,P4,A4,P5,m6,M6,m7,M7', 'ascending',  'name_4choice',  3),
    ('CAT_INT_SC06_P04', 'CAT_INT_SC06_P04_S02', '상행 음정 알아맞히기', 'interval', 'P1,m2,M2,m3,M3,P4,A4,P5,m6,M6,m7,M7', 'ascending',  'interval_subj', 3),
    ('CAT_INT_SC06_P04', 'CAT_INT_SC06_P04_S03', '하행 음정 알아맞히기', 'interval', 'P1,m2,M2,m3,M3,P4,A4,P5,m6,M6,m7,M7', 'descending', 'interval_subj', 3),
    ('CAT_INT_SC06_P04', 'CAT_INT_SC06_P04_S04', '건반에서 음정 선택',   'interval', 'P1,m2,M2,m3,M3,P4,A4,P5,m6,M6,m7,M7', 'ascending',  'keyboard_subj', 3),
    ('CAT_INT_SC06_P04', 'CAT_INT_SC06_P04_S05', '화음에서 음정 찾기',   'interval', 'P1,m2,M2,m3,M3,P4,A4,P5,m6,M6,m7,M7', 'harmonic',   'interval_subj', 3),
]

# ══════════════════════════════════════════════════════════════════════════════
# 룩업 테이블 (O(1) 조회)
# ══════════════════════════════════════════════════════════════════════════════
CURRICULUM_COLS = ['part_id', 'step_id', 'step_name', 'question_type',
                   'note_pool', 'direction', 'answer_type', 'difficulty_level']

STEP_LOOKUP: dict = {r[1]: dict(zip(CURRICULUM_COLS, r)) for r in CURRICULUM_DATA}
ALL_STEP_IDS: list = [r[1] for r in CURRICULUM_DATA]

VALID_CATEGORY_PREFIXES = ('CAT_SN', 'CAT_INT')

# ── CAT_INT 전체복습 파트 → 누적 step_id 리스트 매핑 ─────────────────────────
_int_review_part_ids = [
    row[1]
    for row in PART_DATA
    if row[0].startswith('CAT_INT') and '전체복습' in row[2]
]

INT_REVIEW_EXPANSION: dict = {}
_cumulative: list = []
for _i, _pid in enumerate(_int_review_part_ids):
    if _i == 0:
        _course_prefix = _pid.rsplit('_P', 1)[0]
        _cumulative = [sid for sid in ALL_STEP_IDS if sid.startswith(_course_prefix + '_')]
    else:
        _part_steps = [sid for sid in ALL_STEP_IDS if sid.startswith(_pid + '_')]
        _cumulative = _cumulative + _part_steps
    INT_REVIEW_EXPANSION[_pid] = list(_cumulative)
