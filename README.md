# EarGenX

EarGenX(eargenx.py)는 **청음 문제 데이터 생성기**입니다.
음악 교육 플랫폼 Golden Ear에서서 사용하는 청음 연습 문제를 커리큘럼 계층 구조에 따라 자동으로 생성합니다.

---

## 설치

Python 3이 필요합니다.

```bash
pip install -r requirements.txt
```

> `pandas`, `openpyxl`이 없으면 `print` / `md` 출력은 그대로 사용할 수 있고, `csv` / `xlsx` 출력만 비활성화됩니다.

---

## 기본 사용법

```bash
# 랜덤 스텝에서 10문제, 콘솔 출력 (기본값)
python eargenx.py

# 특정 코스에서 20문제
python eargenx.py --range CAT_SN_SC01 --amount 20

# 여러 범위를 한 플래그에 공백으로 지정
python eargenx.py -r CAT_INT_SC06_P04_S03 CAT_INT_SC06_P04_S04 -a 5

# 플래그 반복으로 여러 범위 지정 (동일 결과)
python eargenx.py -r CAT_SN -r CAT_INT -a 10 -f xlsx csv

# 특정 스텝, 시드 고정으로 재현 가능한 문제 생성
python eargenx.py -r CAT_SN_SC01_P03_S04 -a 5 --seed 42

# 계단식 난이도 커브 적용
python eargenx.py -r CAT_INT_SC01_P01 --difficulty stairs
```

---

## CLI 옵션

| 옵션 | 약어 | 설명 | 기본값 |
|------|------|------|--------|
| `--range RANGE ...` | `-r` | 문제 범위 지정 (공백 또는 플래그 반복으로 여러 개 가능) | 랜덤 스텝 |
| `--amount N` | `-a` | 범위당 문제 수 | `10` |
| `--difficulty MODE` | `-d` | 난이도 설정 (아래 참고) | 스텝 기본값 |
| `--shuffle` | `-s` | 생성된 문제 순서 무작위화 | 비활성 |
| `--format FMT ...` | `-f` | 출력 형식 (복수 지정 가능) | `print` |
| `--output PATH` | `-o` | 파일 저장 경로 | `example/` |
| `--seed N` | | 재현을 위한 랜덤 시드 | 없음 |

### `--difficulty` 값

| 값 | 설명 |
|----|------|
| `1` / `2` / `3` | 고정 난이도 (쉬움 / 보통 / 어려움) |
| `linear` | 1→3 선형 증가 커브 |
| `stairs` | 계단식 증가 커브 |
| `fixed` | 스텝에 정의된 기본 난이도 고정 |

### `--format` 값

| 값 | 설명 |
|----|------|
| `print` | 콘솔 테이블 출력 |
| `csv` | CSV 파일 저장 |
| `xlsx` | Excel 파일 저장 |
| `md` | Markdown 테이블 파일 저장 |

---

## 범위(Range) 지정 방법

범위는 커리큘럼 계층의 어느 단계든 지정할 수 있습니다.

```
CAT_SN                      → 단일음 전체 (모든 코스·파트·스텝)
CAT_SN_SC01                 → 단일음 7음계 코스 전체
CAT_SN_SC01_P01             → 파트 전체
CAT_SN_SC01_P01_S01         → 특정 스텝 하나
CAT_INT                     → 음정 전체
CAT_INT_SC03_P02            → 음정 코스3 파트2 전체
```

여러 범위를 지정하는 방법은 두 가지이며 결과는 동일합니다.

```bash
# 공백으로 한 번에 (새로운 방식)
python eargenx.py -r CAT_INT_SC06_P04_S03 CAT_INT_SC06_P04_S04

# 플래그 반복 (기존 방식)
python eargenx.py -r CAT_INT_SC06_P04_S03 -r CAT_INT_SC06_P04_S04

# 혼합도 가능
python eargenx.py -r CAT_SN_SC01 -r CAT_INT_SC06_P04_S03 CAT_INT_SC06_P04_S04
```

---

## 커리큘럼 구조

```
카테고리 (Category)
├── CAT_SN  — 단일음
│   ├── SC01  7음계 (파트 P01~P06)
│   └── SC02  12음계 (파트 P01~P09)
└── CAT_INT — 음정
    ├── SC01  코스1: 1도, 2도 (P01~P03)
    ├── SC02  코스2: 2도, 3도 (P01~P04)
    ├── SC03  코스3: 3도, 4도 (P01~P04)
    ├── SC04  코스4: 4도, 5도 (P01~P03)
    ├── SC05  코스5: 3도, 6도 (P01~P04)
    └── SC06  코스6: 2도, 7도 (P01~P04)
```

각 파트는 여러 **스텝(Step)**으로 구성되며, 스텝마다 문제 유형과 답변 방식이 다릅니다.

### 문제 유형 (answer_type)

| 유형 | 설명 |
|------|------|
| `same_diff` | 두 음/음정이 같은지 다른지 판별 |
| `name_2choice` | 음이름/음정 이름 2지선다 |
| `name_3choice` | 음이름/음정 이름 3지선다 |
| `name_4choice` | 음이름/음정 이름 4지선다 |
| `height_compare` | 다양한 높이로 제시된 음정 비교 |
| `interval_subj` | 음정 이름 주관식 (상행/하행/화음) |
| `keyboard_subj` | 음정 이름 제시 → 건반에서 선택 |
| `piano_subj` | 단일음 → 피아노 건반 직접 입력 |

### 난이도 규칙

| 레벨 | 이름 | 옥타브 범위 | 오답 배치 전략 |
|------|------|------------|---------------|
| 1 | 쉬움 | 4옥타브 고정 | 정답과 멀리 (≥5반음) |
| 2 | 보통 | 3~5옥타브 | 무작위 배치 |
| 3 | 어려움 | 3~6옥타브 | 정답과 가까이 (≤2반음) |

---

## 음정 기호 표기

| 기호 | 한국어 | 반음 수 |
|------|--------|---------|
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

---

## 출력 예시

```bash
python eargenx.py -r CAT_SN_SC01_P01 -a 3 -f print
```

```
step_id                    | answer | choices       | present_notes | ...
CAT_SN_SC01_P01_S01        | C4     | —             | ['C4', 'F4']  | ...
CAT_SN_SC01_P01_S02        | F4     | ['C4', 'F4']  | ['F4']        | ...
CAT_SN_SC01_P01_S03        | C4     | ['C4', 'F4']  | ['C4']        | ...
```

파일 저장 시 타임스탬프가 포함된 파일명으로 `example/` 폴더에 저장됩니다.
예: `example/eargenx_20260226_153045.xlsx`
