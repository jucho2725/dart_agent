# DART 에이전트 시스템

DART(전자공시시스템) 데이터를 수집하고 분석하는 AI 에이전트 시스템입니다.

## 🚀 주요 기능

### 1. 데이터 수집 (OpendartAgent)
- 회사명으로 DART 고유번호 검색
- 재무제표 데이터 자동 수집
- DataFrame 자동 변환 및 저장

### 2. 데이터 저장 (SessionDataStore)
- 메모리 기반 DataFrame 저장소
- 키-값 기반 데이터 관리
- CSV/JSON 내보내기 지원

### 3. 다중 데이터 분석 (AnalyzeAgent) ✨ NEW
- 여러 DataFrame 동시 분석
- 연도별/회사별 비교 분석
- 재무비율 자동 계산
- 사용자 정의 분석 코드 실행
- **계정명 자동 매핑** - 회사/연도별로 다른 계정명 자동 인식

### 4. 통합 워크플로우 (LangGraph) 🎯 NEW
- **PlannerAgent**: 사용자 요청을 분석하여 적절한 에이전트로 라우팅
- **상태 기반 워크플로우**: 대화 맥락을 유지하며 다단계 작업 처리
- **자동 에이전트 선택**: 데이터 수집/분석 작업 자동 판단
- **Multi-turn 대화**: 연속적인 대화 처리 지원

## 📋 요구사항

- Python 3.8+
- OpenAI API 키
- DART API 키

## 🛠️ 설치

1. 의존성 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
`.env` 파일을 생성하고 다음 내용을 추가하세요:
```
OPENAI_API_KEY=your_openai_api_key
DART_API_KEY=your_dart_api_key
```

## 💻 사용법

### 1. 통합 워크플로우 사용 (권장) 🎯

```python
from agent.graph import run_dart_workflow

# 간단한 사용법
result = run_dart_workflow("삼성전자 2024년 재무제표 분석해줘")

# 또는 대화형 데모 실행
python demo_workflow.py --interactive
```

### 2. 개별 에이전트 사용

#### 데이터 수집

```python
from utils.data_store import SessionDataStore
from agent.opendart_agent import create_opendart_agent

# 데이터 저장소 초기화
store = SessionDataStore()

# 데이터 수집 에이전트 생성
agent = create_opendart_agent(store)

# 재무제표 조회
result = agent.invoke({
    "input": "삼성전자 2023년 연결 재무제표 조회해줘"
})
```

### 3. 다중 데이터 분석 (NEW)

```python
from agent.analyze_agent import create_multi_df_analyze_agent

# 분석 에이전트 생성
analyze_agent = create_multi_df_analyze_agent(store)

# 매출액 성장률 분석
result = analyze_agent.invoke({
    "input": "2023년 대비 2024년 매출액 성장률을 계산해줘"
})

# 회사 간 비교
result = analyze_agent.invoke({
    "input": "삼성전자와 LG전자의 2023년 재무상태를 비교 분석해줘"
})
```

### 3. 데모 실행

```bash
# 기본 데모
python demo_analyze_agent.py

# 대화형 모드
python demo_analyze_agent.py --interactive
```

## 🏗️ 프로젝트 구조

```
dart/
├── agent/           # 에이전트 구현
│   ├── opendart_agent.py    # 데이터 수집 에이전트
│   ├── analyze_agent.py     # 데이터 분석 에이전트
│   └── graph.py            # LangGraph 워크플로우
├── tools/           # LangChain 도구
│   ├── opendart/           # OpenDART API 도구
│   └── analysis_tools.py   # 분석 도구
├── utils/           # 유틸리티
│   └── data_store.py       # DataFrame 저장소
├── resources/       # 리소스
│   ├── config.py          # 설정 관리
│   ├── prompt_loader.py   # 프롬프트 로더
│   └── prompt/           # 프롬프트 파일
│       ├── planner/      # PlannerAgent 프롬프트
│       ├── opendart/     # OpendartAgent 프롬프트
│       └── analyze/      # AnalyzeAgent 프롬프트
└── tests/          # 테스트
    ├── test_data_store.py
    ├── test_analyze_agent.py
    └── test_workflow.py    # 워크플로우 테스트
```

## 🧪 테스트

```bash
# 데이터 저장소 테스트
python tests/test_data_store.py

# DataFrame 저장 테스트
python tests/test_dataframe_storage.py

# 분석 에이전트 테스트
python tests/test_analyze_agent.py
```

## 📊 지원 기능

### 재무제표 분석
- 매출액, 영업이익, 당기순이익 등 주요 지표 추출
- 부채비율, 자기자본비율 등 재무비율 계산
- 연도별 성장률 분석
- 회사 간 비교 분석

### 데이터 형식
- 연결재무제표 (CFS)
- 개별재무제표 (OFS)
- 분기별/연도별 데이터

## 🤝 기여하기

이슈 및 PR은 언제든 환영합니다!

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 
