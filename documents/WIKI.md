# EarGenX 코드 위키

> **EarGenX**는 음악 교육용 청음(ear training) 문제를 자동으로 생성하는 Python CLI 도구입니다.
> 전체 로직이 단일 파일 `eargenx.py` (~1,375줄) 에 집약되어 있으며, 13개의 섹션으로 구성됩니다.

---

## 목차

1. [전체 구조 개요](#1-전체-구조-개요)
2. [실행 흐름 (main 함수)](#2-실행-흐름-main-함수)
3. [커리큘럼 데이터 구조](#3-커리큘럼-데이터-구조)
4. [음악 유틸리티 (MIDI ↔ 음이름)](#4-음악-유틸리티-midi--음이름)
5. [문제 타입 규칙 (ANSWER_TYPE_RULES)](#5-문제-타입-규칙-answer_type_rules)
6. [난이도 규칙 (DIFFICULTY_RULES)](#6-난이도-규칙-difficulty_rules)
7. [SingleNoteGenerator (단일음 생성기)](#7-singlenotegenerator-단일음-생성기)
8. [IntervalGenerator (음정 생성기)](#8-intervalgenerator-음정-생성기)
9. [배치 생성 (generate_batch / generate_all_exhaustive)](#9-배치-생성)
10. [범위 해석 (resolve_range)](#10-범위-해석-resolve_range)
11. [출력 포맷터](#11-출력-포맷터)
12. [CLI 인터페이스](#12-cli-인터페이스)
13. [데이터 흐름 다이어그램](#13-데이터-흐름-다이어그램)
14. [커리큘럼 전체 목록](#14-커리큘럼-전체-목록)

---

## 1. 전체 구조 개요

`eargenx.py` 는 다음 13개 섹션으로 구성됩니다.

| 섹션 | 내용 | 주요 심볼 |
|------|------|-----------|
| 1 | 시스템 상수 | `MIDI_MIN=48(C3)`, `MIDI_MAX=84(C6)` |
| 2 | 커리큘럼 데이터 | `CATEGORY_DATA`, `COURSE_DATA`, `PART_DATA`, `CURRICULUM_DATA` |
| 3 | 룩업 테이블 + 규칙 | `STEP_LOOKUP`, `ANSWER_TYPE_RULES`, `DIFFICULTY_RULES` |
| 4 | 음 유틸리티 | `note_to_midi()`, `midi_to_note()`, `parse_pool()` 등 |
| 5 | SingleNoteGenerator | 단일음 문제 생성 클래스 |
| 6 | IntervalGenerator | 음정 문제 생성 클래스 |
| 7 | 난이도 곡선 | `difficulty_curve()` |
| 8 | 범위 해석 | `resolve_range()` |
| 9 | 배치 생성 | `generate_batch()`, `generate_all_exhaustive()` |
| 10 | 레코드 → 행 변환 | `record_to_row()` |
| 11 | 출력 포맷터 | `output_print()`, `output_csv()`, `output_xlsx()`, `output_md()` |
| 12 | CLI | `build_parser()`, `parse_difficulty()` |
| 13 | main | `main()` |

---

## 2. 실행 흐름 (main 함수)

`main()` 은 다음 5단계를 순서대로 실행합니다.

```
1. 범위 결정
   ├─ --range 없음 → 랜덤 스텝 1개 자동 선택
   └─ --range 있음 → resolve_range()로 step_id 목록 확보

2. 난이도 파싱
   └─ parse_difficulty() → (diff_mode, fixed_level) 튜플

3. 문제 생성
   ├─ --all 플래그 → generate_all_exhaustive() (가능한 모든 문제)
   └─ 일반          → generate_batch() (지정 개수)

4. 셔플 (--shuffle 옵션)
   └─ random.shuffle() + 번호 재정렬

5. 출력
   └─ 각 포맷(print/csv/xlsx/md)별 output_* 함수 호출
```

---

## 3. 커리큘럼 데이터 구조

### 계층 구조

```
Category (CAT_SN / CAT_INT)
└── Course  (CAT_SN_SC01, CAT_INT_SC02 ...)
    └── Part   (CAT_SN_SC01_P01 ...)
        └── Step   (CAT_SN_SC01_P01_S01 ...)
```

ID는 항상 상위 계층을 접두사로 포함합니다. 예: `CAT_INT_SC03_P02_S05`

### CATEGORY_DATA

```python
[
    ('CAT_SN',  '단일음'),
    ('CAT_INT', '음정'),
]
```

### COURSE_DATA (8개 코스)

| course_id | 이름 | 설명 |
|-----------|------|------|
| CAT_SN_SC01 | 7음계 | C D E F G A B |
| CAT_SN_SC02 | 12음계 | 반음계 포함 전체 |
| CAT_INT_SC01 | 코스1 | 1도, 2도 |
| CAT_INT_SC02 | 코스2 | 2도, 3도 |
| CAT_INT_SC03 | 코스3 | 3도, 4도 |
| CAT_INT_SC04 | 코스4 | 4도, 5도 |
| CAT_INT_SC05 | 코스5 | 3도, 6도 |
| CAT_INT_SC06 | 코스6 | 2도, 7도 |

### CURRICULUM_DATA (스텝 정의)

각 스텝은 다음 8개 컬럼으로 구성됩니다.

```python
(part_id, step_id, step_name, question_type, note_pool, direction, answer_type, difficulty_level)
```

| 컬럼 | 설명 | 예시 |
|------|------|------|
| `part_id` | 소속 파트 ID | `CAT_SN_SC01_P01` |
| `step_id` | 고유 스텝 ID | `CAT_SN_SC01_P01_S03` |
| `step_name` | 스텝 이름 | `음이름` |
| `question_type` | 문제 유형 | `single_note` / `interval` |
| `note_pool` | 사용 음/음정 풀 | `C,F` / `P1,M2` |
| `direction` | 방향 (음정 전용) | `ascending` / `descending` / `harmonic` / `-` |
| `answer_type` | 정답 방식 키 | `same_diff`, `name_4choice`, `interval_subj` 등 |
| `difficulty_level` | 기본 난이도 | `1` / `2` / `3` |

### STEP_LOOKUP 딕셔너리

```python
STEP_LOOKUP: dict = {
    r[1]: dict(zip(CURRICULUM_COLS, r))
    for r in CURRICULUM_DATA
}
```

`step_id` → 스텝 dict 로 **O(1)** 조회가 가능합니다.

---

## 4. 음악 유틸리티 (MIDI ↔ 음이름)

### MIDI 음번호 체계

| MIDI 번호 | 음 | 옥타브 |
|-----------|-----|--------|
| 48 | C3 | 최솟값 (`MIDI_MIN`) |
| 60 | C4 | 중간 C (옥타브 기준) |
| 84 | C6 | 최댓값 (`MIDI_MAX`) |

### NOTE_NAMES (12음)

```python
['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'G#', 'A', 'Bb', 'B']
```

인덱스 0~11이 음이름 인덱스입니다. `midi % 12` 로 피치 클래스를 구합니다.

### ENHARMONIC_MAP (이명동음 정규화)

```python
{'Db': 'C#', 'D#': 'Eb', 'Gb': 'F#', 'Ab': 'G#', 'A#': 'Bb', 'Cb': 'B', 'E#': 'F'}
```

`Db`와 `C#`처럼 같은 음을 다른 이름으로 부르는 경우를 통일합니다.

### 핵심 변환 함수

#### `note_to_midi(note_with_octave: str) → int`

```
"C4" → (4+1)*12 + 0 = 60
"F#3" → (3+1)*12 + 6 = 54
```

#### `midi_to_note(midi: int) → str`

```
60 → "C4"   (60//12 - 1 = 4, 60%12 = 0 → 'C')
61 → "C#4"
```

#### `pool_to_midi_range(pool, octaves) → list`

음이름 목록 + 옥타브 목록을 조합하여, `MIDI_MIN~MIDI_MAX` 범위 내 MIDI 번호 정렬 목록을 반환합니다.

```python
pool_to_midi_range(['C', 'F'], [4]) → [60, 65]
```

### INTERVAL_SEMITONES (12개 음정)

| 기호 | 이름 | 반음 수 |
|------|------|---------|
| P1 | 완전1도 | 0 |
| m2 | 단2도 | 1 |
| M2 | 장2도 | 2 |
| m3 | 단3도 | 3 |
| M3 | 장3도 | 4 |
| P4 | 완전4도 | 5 |
| A4 | 증4도 | 6 |
| P5 | 완전5도 | 7 |
| m6 | 단6도 | 8 |
| M6 | 장6도 | 9 |
| m7 | 단7도 | 10 |
| M7 | 장7도 | 11 |

#### `build_interval_midi(root_midi, symbol, direction) → int`

- `ascending`: `root_midi + 반음수`
- `descending`: `root_midi - 반음수`
- `harmonic`: 두 음을 동시에 → 내부적으로 `ascending`과 동일하게 계산

#### `octave_difficulty(ref_midi) → float`

C4(MIDI 60)에서 옥타브 거리가 멀수록 어렵다는 수치를 반환합니다 (1.0~3.0).

---

## 5. 문제 타입 규칙 (ANSWER_TYPE_RULES)

```python
ANSWER_TYPE_RULES = {
    answer_type: (label, num_choices, present_count, distractor_strategy, pool_size_rule)
}
```

| answer_type | label | 선택지 수 | 제시음 수 | 오답 전략 |
|-------------|-------|-----------|-----------|-----------|
| `same_diff` | 같음/다름 | 2 | 2 | none |
| `name_2choice` | 이름 2지선다 | 2 | 1 | asc_by_distance |
| `name_3choice` | 이름 3지선다 | 3 | 1 | use_all |
| `name_4choice` | 이름 4지선다 | 4 | 1 | asc_by_distance |
| `height_compare` | 다양한 높이 비교 | 2 | 2 | none |
| `interval_subj` | 음정 주관식 | 0 (주관식) | 1 | none |
| `keyboard_subj` | 건반 선택 | 0 (주관식) | 1 | none |
| `piano_subj` | 피아노 주관식 | 0 (주관식) | 1 | none |

### 각 타입 설명

- **same_diff**: 두 음(또는 두 음정)을 들려주고 "같음"/"다름" 중 선택
- **name_2choice**: 1개 음을 듣고 음이름 2개 중 선택
- **name_3choice**: 3개 중 선택 (음정 풀이 3개일 때 전용)
- **name_4choice**: 4개 중 선택
- **height_compare**: 같은 음정을 다른 높이에서 들려주고 "같음"/"다름" 판별
- **interval_subj**: 음정을 듣고 두 음이름을 직접 기재 (주관식)
- **keyboard_subj**: 기준음과 음정이름을 주면 건반에서 목표음을 선택
- **piano_subj**: 단일음을 듣고 건반에서 음이름 직접 입력

---

## 6. 난이도 규칙 (DIFFICULTY_RULES)

```python
DIFFICULTY_RULES = {
    level: (label, octaves, proximity_strategy, proximity_semitones)
}
```

| 레벨 | 이름 | 옥타브 범위 | 오답 배치 전략 |
|------|------|-------------|----------------|
| 1 | 쉬움 | [4] (4옥타브만) | desc_by_distance (오답 멀리) |
| 2 | 보통 | [3, 5] (3 또는 5옥타브) | shuffle (무작위) |
| 3 | 어려움 | [3, 4, 5, 6] (전 범위) | asc_by_distance (오답 가까이) |

### proximity_strategy (오답 배치 전략)

- **desc_by_distance**: 오답을 정답과 가장 **먼** 음부터 배치 → 쉬움 (구분하기 쉬움)
- **asc_by_distance**: 오답을 정답과 가장 **가까운** 음부터 배치 → 어려움 (헷갈림)
- **shuffle**: 무작위 배치

### 난이도 곡선 (`difficulty_curve`)

`--difficulty` 플래그 값에 따라 문제 목록별 난이도 레벨 배열을 생성합니다.

| 모드 | 설명 | 예시 (10문제) |
|------|------|--------------|
| `linear` | 1→2→3 선형 증가 | [1,1,1,1,2,2,2,3,3,3] |
| `stairs` | 40% Lv1 → 30% Lv2 → 30% Lv3 계단식 | [1,1,1,1,2,2,2,3,3,3] |
| `fixed` | 고정 레벨 | [2,2,2,2,2,2,2,2,2,2] |
| `1`/`2`/`3` | fixed 레벨 단축 표기 | 위와 동일 |

---

## 7. SingleNoteGenerator (단일음 생성기)

단일음(`question_type == 'single_note'`) 문제를 생성하는 클래스입니다.

### 초기화

```python
gen = SingleNoteGenerator(seed=42)
```

- `rng`: 시드 기반 `random.Random` 인스턴스
- `_session_history`: `{step_id: [answer_midi, ...]}` 딕셔너리 — 직전 정답을 추적

### `generate(step_id, difficulty_level) → dict`

```
1. STEP_LOOKUP[step_id] 로 스텝 정보 조회
2. _get_answer_rule() / _get_difficulty_rule() 로 규칙 dict 생성
3. pool_to_midi_range() 로 MIDI 풀 생성
4. _pick_answer() 로 정답 음 선택 (연속 3회 방지)
5. answer_type에 따라 분기:
   ├─ same_diff    → _build_same_diff()
   ├─ piano_subj   → present_notes=[answer], choices=None
   └─ 그 외        → _build_choices()
6. _session_history 에 answer_midi 기록
7. 결과 dict 반환
```

### 반환 dict 구조 (단일음)

```python
{
    'step_id':          'CAT_SN_SC01_P01_S03',
    'step_name':        '음이름',
    'question_type':    'single_note',
    'answer_type':      'name_2choice',
    'direction':        '-',
    'difficulty_level': 1,
    'answer':           'C4',
    'answer_midi':      60,
    'present_notes':    ['C4'],
    'choices':          ['F4', 'C4'],   # 셔플됨
    'total_difficulty': 1.0,
}
```

### `_pick_answer()` — 연속 정답 방지

```
최근 history 확인:
  - 마지막 2개가 동일하면 → 해당 음을 excluded_set에 추가
  - 그 외 음에서 무작위 선택
  - 후보가 없으면 → excluded 무시하고 전체에서 선택
```

### `_build_same_diff()` — 같음/다름 문제

```
50% 확률로 같음/다름 결정
- 같음: [first, first], '같음'
- 다름: 다른 음이름 & 12반음 이내 → [first, second], '다름'
```

### `_build_choices()` — 오답 보기 생성

```
1. 정답과 다른 음이름만 candidates 로 추출
2. pool≤2 또는 use_all → distractor_pool = candidates 전체
3. 그 외 → _sort_by_proximity() 로 전략 적용
4. _pick_unique_name() 로 음이름 기준 중복 제거하며 n개 추출
5. [정답] + [오답들] → shuffle
```

---

## 8. IntervalGenerator (음정 생성기)

음정(`question_type == 'interval'`) 문제를 생성하는 클래스입니다.

### `generate(step_id, difficulty_level) → dict`

```
1. STEP_LOOKUP, answer_rule, difficulty_rule 조회
2. _pick_root_and_interval() → (root_midi, symbol)
3. upper_midi = build_interval_midi(root_midi, symbol, direction)
4. answer_type에 따라 분기:
   ├─ same_diff      → _build_same_diff() (4음 제시)
   ├─ height_compare → _build_height_compare() (4음 제시, 다른 높이)
   ├─ interval_subj / keyboard_subj → present_notes=[root_note, upper_note]
   └─ name_Xchoice  → _build_name_choices() (음정 이름 보기)
5. _session_history 에 (root_midi, symbol) 기록
6. 결과 dict 반환
```

### 반환 dict 구조 (음정)

```python
{
    'step_id':            'CAT_INT_SC01_P01_S04',
    'step_name':          '상행 음정 알아맞히기',
    'question_type':      'interval',
    'answer_type':        'interval_subj',
    'direction':          'ascending',
    'difficulty_level':   1,
    'answer_interval':    'M2',
    'answer_interval_ko': '장2도',
    'root_midi':          60,
    'root_note':          'C4',
    'upper_midi':         62,
    'upper_note':         'D4',
    'present_notes':      ['C4', 'D4'],
    'choices':            None,   # 주관식
    'total_difficulty':   1.0,
}
```

### `_pick_root_and_interval()` — 연속 음정 방지

```
candidates = (root_midi, symbol) 모든 조합 중
  - 마지막 2개의 symbol이 동일하면 해당 symbol 제외
  - MIDI_MIN ≤ upper_midi ≤ MIDI_MAX 를 만족하는 것만
  → random.choice()
```

### `_build_same_diff()` vs `_build_height_compare()`

| | `_build_same_diff` | `_build_height_compare` |
|---|---|---|
| 같음일 때 | 정확히 동일한 4음 | 같은 음정, **다른 기준음(높이)** |
| 다름일 때 | 같은 기준음, 다른 음정 종류 | 다른 기준음 + 다른 음정 종류 |
| 목적 | 음정 종류 판별 | 음정 종류 + 높이 판별 |

### `_build_name_choices()` — 음정 이름 보기

```
target_st = 정답 음정의 반음수
pool_syms = 정답 제외한 풀 내 음정들
  - asc_by_distance: 반음 거리 오름차순 (헷갈리는 것 먼저)
  - desc_by_distance: 반음 거리 내림차순
  - shuffle: 무작위
distractors = 앞에서 (num_choices-1)개 선택
choices = [정답 이름] + [오답 이름들] → shuffle
```

---

## 9. 배치 생성

### `generate_batch(step_ids, amount, diff_mode, fixed_level, seed)`

랜덤 문제 세트를 지정 개수만큼 생성합니다.

```
1. difficulty_curve(amount, mode=diff_mode) → levels 목록
2. rng.choice(step_ids) 로 매 문제마다 step 무작위 선택
3. question_type 확인:
   - single_note → sn_gen.generate()
   - interval    → int_gen.generate()
4. q['q_num'] = i 번호 부여
5. records 반환
```

### `generate_all_exhaustive(step_ids, seed)`

지정 범위 내 **가능한 모든 경우의 수**를 빠짐없이 생성합니다. `--all` 플래그 사용 시 호출됩니다.

```
FULL_OCTAVES = [3, 4, 5, 6]  # 난이도 무관, 전 옥타브

단일음:
  midi_pool 내 모든 answer_midi 순회
  - same_diff: answer_midi마다 '같음' 1개 + '다름' (12반음 이내 다른 음) n개
  - piano_subj: 음마다 1문제
  - name_Xchoice: 음마다 1문제

음정:
  (root_midi, symbol) 유효 쌍 전체 순회
  - same_diff: 쌍마다 '같음' 1개 + '다름' (ipool 내 다른 symbol) n개
  - height_compare: 쌍마다 다른 높이(alt_root) 조합 전체
  - interval_subj/keyboard_subj: 쌍마다 1문제
  - name_Xchoice: 쌍마다 1문제
```

---

## 10. 범위 해석 (resolve_range)

```python
resolve_range(range_str: str) → list[str]
```

계층적 범위 ID를 step_id 목록으로 변환합니다.

```
'CAT_SN'                → CURRICULUM_DATA 중 step_id가 'CAT_SN_' 로 시작하는 모든 것
'CAT_SN_SC01'           → 'CAT_SN_SC01_' 접두사를 가진 모든 스텝
'CAT_SN_SC01_P01'       → 'CAT_SN_SC01_P01_' 접두사를 가진 모든 스텝
'CAT_SN_SC01_P01_S01'   → 정확히 해당 스텝 1개 (STEP_LOOKUP 직접 조회)
```

**유효성 검사**:
- `CAT_SN` 또는 `CAT_INT` 로 시작하지 않으면 `ValueError`
- 매칭되는 스텝이 없으면 `ValueError`

---

## 11. 출력 포맷터

### `record_to_row(q, range_label) → dict`

생성기에서 반환된 문제 dict를 출력 테이블 행으로 변환합니다.

| 출력 컬럼 | 설명 |
|-----------|------|
| `#` | 문제 번호 |
| `range` | 범위 레이블 |
| `step_id` | 스텝 ID |
| `step_name` | 스텝 이름 |
| `question_type` | single_note / interval |
| `answer_type` | 정답 방식 |
| `direction` | ascending / descending / harmonic / - |
| `difficulty` | Lv.1 (쉬움) 형태 |
| `present` | 제시 음/음정 문자열 |
| `answer` | 정답 문자열 |
| `choices` | 선택지 (주관식이면 "(주관식)") |

**`present` 문자열 조합 규칙**:
- `ascending/descending`: `C4 → D4`
- `harmonic`: `C4 + E4`
- 4음 (same_diff/height_compare): `C4 → D4 | C4 → E4`
- `keyboard_subj`: `C4 | M2 (장2도)` (기준음 | 음정이름)

### `output_print(rows)`

터미널에 정렬된 텍스트 테이블로 출력합니다.

### `output_csv(rows, filepath)`

UTF-8 BOM 인코딩 CSV 파일로 저장합니다 (한글 Excel 호환).

### `output_xlsx(rows, filepath)`

pandas + openpyxl을 사용해 Excel 파일로 저장합니다.
패키지 미설치 시 경고 메시지와 함께 건너뜁니다.

### `output_md(rows, filepath)`

GitHub Flavored Markdown 테이블 형식으로 저장합니다.

---

## 12. CLI 인터페이스

### 인수 목록

| 플래그 | 기본값 | 설명 |
|--------|--------|------|
| `-r, --range` | 없음 (랜덤 스텝) | 범위 ID (반복/공백 분리 가능) |
| `-a, --amount` | 10 | 범위당 문제 개수 |
| `-d, --difficulty` | `linear` | 난이도: `1`/`2`/`3` 또는 `linear`/`stairs`/`fixed` |
| `-s, --shuffle` | False | 전체 문제 셔플 |
| `-f, --format` | `print` | 출력 포맷 (복수 가능): `print csv xlsx md` |
| `-o, --output` | `example/` | 파일 저장 경로 |
| `--seed` | None | 재현 가능한 랜덤 시드 |
| `-A, --all` | False | 가능한 모든 문제 생성 (`--amount` 무시) |

### 사용 예시

```bash
# 기본 실행 (랜덤 스텝, 10문제, 터미널 출력)
python eargenx.py

# 단일음 7음계 코스에서 20문제, xlsx 출력
python eargenx.py -r CAT_SN_SC01 -a 20 -f xlsx

# 두 범위를 각 10문제씩, xlsx + csv 동시 출력
python eargenx.py -r CAT_SN -r CAT_INT -a 10 -f xlsx csv

# 특정 스텝, 고정 seed로 재현 가능한 결과
python eargenx.py -r CAT_SN_SC01_P03_S04 -a 5 --seed 42

# 음정 SC01_P01에서 계단식 난이도, 셔플
python eargenx.py -r CAT_INT_SC01_P01 --difficulty stairs --shuffle

# 특정 범위의 모든 가능한 문제 생성
python eargenx.py -r CAT_INT_SC02_P01 --all -f csv
```

---

## 13. 데이터 흐름 다이어그램

```
CLI 인수 파싱
     │
     ▼
resolve_range(range_str)
     │  step_id 목록
     ▼
difficulty_curve(amount, mode)
     │  [level, level, ...]
     ▼
generate_batch() 또는 generate_all_exhaustive()
     │
     ├── rng.choice(step_ids)
     │         │ step_id
     │         ▼
     │   STEP_LOOKUP[step_id]  ←────── CURRICULUM_DATA
     │         │ step 정보
     │         ▼
     │   question_type == 'single_note'?
     │     ├── YES → SingleNoteGenerator.generate()
     │     │             │
     │     │             ├── pool_to_midi_range()
     │     │             ├── _pick_answer()  (연속 방지)
     │     │             └── _build_choices() / _build_same_diff()
     │     │
     │     └── NO  → IntervalGenerator.generate()
     │                   │
     │                   ├── _pick_root_and_interval()  (연속 방지)
     │                   ├── build_interval_midi()
     │                   └── _build_name_choices() / _build_same_diff() / _build_height_compare()
     │
     ▼
record_to_row(q, range_label)
     │ 출력용 행 dict
     ▼
[셔플] (--shuffle)
     │
     ▼
output_print() / output_csv() / output_xlsx() / output_md()
```

---

## 14. 커리큘럼 전체 목록

### CAT_SN — 단일음

#### SC01: 7음계 (6파트)

| 파트 | 음 풀 | 스텝 유형 |
|------|-------|-----------|
| P01 | C, F | same_diff / name_2choice / piano_subj |
| P02 | C, F, G | same_diff / name_2choice / piano_subj |
| P03 | C, D, F, G | same_diff / name_2choice / name_4choice / piano_subj |
| P04 | C, D, E, F, G | same_diff / name_2choice / name_4choice / piano_subj |
| P05 | C, D, E, F, G, A | same_diff / name_2choice / name_4choice / piano_subj |
| P06 | C, D, E, F, G, A, B | same_diff / name_2choice / name_4choice / piano_subj |

#### SC02: 12음계 (9파트)

| 파트 | 음 풀 | 특이사항 |
|------|-------|---------|
| P01 | F, F# | 반음 차이 |
| P02 | C, C# | 반음 차이 |
| P03 | C, C#, F, F# | 조합 |
| P04 | G, G# | 반음 차이 |
| P05 | C, C#, F, F#, G, G# | 조합 |
| P06 | A, Bb, B | 3음 비교, name_3choice 포함 |
| P07 | C, C#, F, F#, G, G#, A, Bb, B | 9음 |
| P08 | D, Eb, E | 3음 비교 |
| P09 | 12음 전체 | 최고 난이도 |

---

### CAT_INT — 음정

각 코스의 구조는 동일합니다:

- **파트 1~3**: 2~3개 음정 비교 (각 파트 7개 스텝)
- **파트 4**: 코스 내 전체 음정 복습 (5개 스텝)

각 파트의 스텝 구성 (7개):

| 스텝 | 유형 |
|------|------|
| S01 | 음정 같음/다름 (`same_diff`) |
| S02 | 다양한 높이 비교 (`height_compare`) |
| S03 | 음정 이름 고르기 (`name_2choice`/`name_3choice`) |
| S04 | 상행 음정 알아맞히기 (`interval_subj`, ascending) |
| S05 | 하행 음정 알아맞히기 (`interval_subj`, descending) |
| S06 | 건반에서 음정 선택 (`keyboard_subj`) |
| S07 | 화음에서 음정 찾기 (`interval_subj`, harmonic) |

복습 파트(P04)의 스텝 구성 (5개):

| 스텝 | 유형 |
|------|------|
| S01 | 음정 이름 고르기 (`name_Xchoice`) |
| S02 | 상행 주관식 (`interval_subj`) |
| S03 | 하행 주관식 (`interval_subj`) |
| S04 | 건반 선택 (`keyboard_subj`) |
| S05 | 화음 주관식 (`interval_subj`) |

#### 코스별 음정 구성

| 코스 | 파트별 음정 풀 |
|------|---------------|
| SC01 | P1,M2 / m2,M2 / P1,m2,M2 |
| SC02 | M2,M3 / M2,m3 / m3,M3 / M2,m3,M3 |
| SC03 | M3,P4 / m3,M3,P4 / P4,A4 / m3,M3,P4,A4 |
| SC04 | P4,P5 / A4,P5 / P4,A4,P5 |
| SC05 | M3,m6 / m3,M6 / m6,M6 / m3,M3,m6,M6 |
| SC06 | M2,m7 / m2,M7 / m7,M7 / m2,M2,m7,M7 |

---

## 부록: 선택적 의존성

| 패키지 | 용도 | 없을 경우 |
|--------|------|-----------|
| `pandas` | XLSX 생성 | XLSX 출력 불가 (경고 표시) |
| `openpyxl` | XLSX 엔진 | XLSX 출력 불가 (경고 표시) |

`print` 와 `md`, `csv` 출력은 표준 라이브러리만으로 동작합니다.

```bash
pip install pandas openpyxl  # XLSX 출력이 필요한 경우
```
