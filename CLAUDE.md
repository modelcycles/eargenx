# CLAUDE.md

이 파일은 Claude Code(claude.ai/code)가 이 저장소의 코드를 다룰 때 참고하는 안내 문서입니다.

## 프로젝트 개요

EarGenX는 음악 교육용 청음 시험 문제를 랜덤 생성하는 단일 파일 Python CLI 도구입니다.
단일음과 음정 두 카테고리를 지원하며, 여러 출력 형식과 난이도 설정이 가능합니다.

## 실행 방법

```bash
# 가상환경 먼저 활성화 (권장)
source .venv/Scripts/activate   # Windows/MINGW64

# 기본 사용 예시
python eargenx.py                                           # 랜덤 스텝, 10문제, print
python eargenx.py -r CAT_SN_SC01 -a 20                    # SC01 코스에서 20문제
python eargenx.py -r CAT_INT -r CAT_SN -a 10 -f xlsx csv  # 복수 범위/형식
python eargenx.py -r CAT_SN_SC01_P03_S04 -a 5 --seed 42   # 재현 가능한 출력
python eargenx.py -r CAT_INT_SC01_P01 --difficulty stairs  # 계단식 난이도 곡선
```

## CLI 인자

| 플래그 | 설명 |
|--------|------|
| `-r, --range` | 계층적 범위 ID (반복 가능): 카테고리 → 코스 → 파트 → 스텝 |
| `-a, --amount` | 범위당 문제 수 (기본값: 10) |
| `-d, --difficulty` | `1`/`2`/`3` (고정) 또는 `linear`/`stairs`/`fixed` (곡선) |
| `-s, --shuffle` | 최종 문제 순서 무작위 섞기 |
| `-f, --format` | `print` / `csv` / `xlsx` / `md` (복수 가능) |
| `-o, --output` | 출력 디렉터리 (기본값: `example/`) |
| `--seed` | 재현 가능한 생성을 위한 정수 시드 |

## 의존성

```bash
pip install -r requirements.txt   # pandas, openpyxl
```

`pandas`/`openpyxl`이 없어도 `print`와 `md` 출력은 정상 동작합니다 (`HAS_PANDAS` / `HAS_OPENPYXL` 플래그로 분기).

## 아키텍처

전체 애플리케이션은 단일 파일(`eargenx.py`, ~1,400줄)에 13개 섹션으로 구성됩니다:

1. **시스템 상수** — MIDI 범위 (C3=48 ~ B5=83)
2. **커리큘럼 데이터** — `PART_DATA`, `CURRICULUM_DATA` 정적 튜플; 카테고리 → 코스 → 파트 → 스텝 계층 (60+ 스텝)
3. **룩업 테이블** — `STEP_LOOKUP`, `ALL_STEP_IDS`, `INT_REVIEW_EXPANSION` (O(1) 조회)
4. **음 유틸** — MIDI ↔ 음이름 변환, 음정 반음 계산, 이명동음 정규화, 음 풀 파싱, `octave_difficulty()`
5. **`SingleNoteGenerator`** — 단일음 문제 생성; 세션 히스토리로 반복 방지; 근접도 기반 오답 생성
6. **`IntervalGenerator`** — 음정 문제 생성 (상행/하행/화음); 난이도에 따라 루트음 범위 조정
7. **난이도 곡선 함수** — `difficulty_curve()` (linear / stairs / fixed 모드)
8. **범위 변환** — `resolve_range()`: 계층 ID 문자열 → step_id 리스트, `INT_REVIEW_EXPANSION` 우선 조회
9. **배치 생성** — `generate_batch()`, `generate_all_exhaustive()` 문제 집합 생성 오케스트레이션
10. **레코드 변환** — 레코드 → 출력용 행 변환 유틸
11. **출력 포맷터** — `output_print()`, `output_csv()`, `output_xlsx()`, `output_md()`
12. **CLI** — `argparse` 기반 `build_parser()`
13. **`main()`** — 최상위 진입점: 인자 파싱 → 범위 변환 → 생성 → 셔플 → 출력

## 커리큘럼 계층

```
카테고리 (CAT_SN / CAT_INT)
└── 코스  (예: CAT_SN_SC01, CAT_INT_SC02)
    └── 파트   (예: CAT_SN_SC01_P01)
        └── 스텝   (예: CAT_SN_SC01_P01_S01)
```

- **CAT_SN** — 단일음 구별 (7음계 SC01, 12음계 SC02)
- **CAT_INT** — 음정 식별 (SC01~SC06, 점진적으로 넓어지는 음정 세트)

각 스텝 정의 포함 항목: 문제 유형, 음/음정 풀, 정답 유형 키, 난이도 레벨.

## INT_REVIEW_EXPANSION (전체복습 파트 누적 확장)

`INT_REVIEW_EXPANSION` 딕셔너리는 CAT_INT 전체복습 파트 ID를 누적 step_id 리스트로 매핑합니다.

| 범위 요청 | 반환 스텝 |
|-----------|-----------|
| `CAT_INT_SC01_P03` | SC01 전체 (P01+P02+P03, 19 스텝) |
| `CAT_INT_SC02_P04` | SC01 전체 + SC02_P04 (24 스텝) |
| `CAT_INT_SC03_P04` | 위 누적 + SC03_P04 (29 스텝) |
| `CAT_INT_SC04_P03` | 위 누적 + SC04_P03 (34 스텝) |
| `CAT_INT_SC05_P04` | 위 누적 + SC05_P04 (39 스텝) |
| `CAT_INT_SC06_P04` | 위 누적 + SC06_P04 (44 스텝) |

비-전체복습 파트 및 코스 단위 요청은 기존과 동일하게 동작합니다.

## 주요 설계 패턴

- **세션 인식 생성**: 두 Generator 모두 배치 내 히스토리를 추적해 즉각적인 반복을 방지합니다.
- **오답 전략**: 난이도 레벨에 따라 오답을 멀리(≥5반음, 쉬움) 또는 가까이(≤2반음, 어려움) 배치합니다.
- **옥타브 난이도**: `octave_difficulty(midi)`가 C4 기준 옥타브 거리로 `total_difficulty`를 계산합니다.
- **데이터 기반 커리큘럼**: 모든 학습 내용은 `CURRICULUM_DATA` 튜플에 인코딩되어 있습니다. 새 스텝 추가 시 행 하나만 추가하면 됩니다.
- **선택적 의존성**: `HAS_PANDAS` / `HAS_OPENPYXL` 플래그로 형식별 코드 경로를 분기합니다.

## 커리큘럼 규칙 보호

**커리큘럼 데이터(`CURRICULUM_DATA`, `PART_DATA`)에 정의된 문제 생성 규칙은 추가·변경·삭제 요청이 명시적으로 있을 때만 수정한다.**
버그 수정, 리팩터링, 기능 추가 등 어떠한 작업 중에도 기존 규칙의 내용(문제 유형, 음/음정 풀, 정답 유형, direction, 난이도 레벨 등)을 임의로 변형해서는 절대 안 된다.

## 깃 커밋 규칙

- **제목**: 항상 영어
- **본문**: 이중 언어 — 한국어 설명 먼저, 영어 설명 뒤

예시:
```
fix: correct height_compare answer/choices bug

- _build_height_compare()에서 항상 '같음'만 반환하던 로직 수정
- Fixed _build_height_compare() to return either '같음' or '다름'
```
