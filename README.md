# DART 데이터 취합 및 분석 에이전트 시스템

DART(Data Analysis, Retrieval & Transfer) 공시 시스템의 재무제표 데이터를 자동으로 수집하고 분석하는 LangChain 기반 Multi-Agent 시스템입니다.

## 주요 기능

- 📊 **재무제표 자동 수집**: OpenDart API를 통한 기업 재무데이터 조회
- 🤖 **지능형 분석**: LangChain Agent를 활용한 자연어 기반 데이터 분석
- 🔄 **Multi-Agent 워크플로우**: LangGraph 기반 복잡한 분석 작업 자동화
- 💾 **세션 데이터 관리**: 수집된 데이터의 체계적인 저장 및 관리
- 🌐 **웹 UI 제공**: Streamlit 기반 직관적인 챗봇 인터페이스

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI                         │
│                  (챗봇 인터페이스)                        │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   LangGraph 워크플로우                    │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Planner   │  │ OpendartAgent │  │AnalyzeAgent │   │
│  │  (라우터)    │  │ (데이터수집)   │  │ (데이터분석)  │   │
│  └─────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  SessionDataStore                       │
│               (DataFrame 중앙 저장소)                     │
└─────────────────────────────────────────────────────────┘
```

## 설치 방법

1. 저장소 클론
```bash
git clone <repository-url>
cd dart
```

2. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
`.env` 파일을 생성하고 다음 API 키를 설정:
```
OPENAI_API_KEY=your_openai_api_key
DART_API_KEY=your_dart_api_key
```

## 사용 방법

### 1. Streamlit UI (권장)

웹 기반 챗봇 인터페이스로 시스템을 사용할 수 있습니다:

```bash
python main.py --streamlit
```

또는 직접 실행:
```bash
streamlit run streamlit/app.py
```

### 2. 콘솔 모드

터미널에서 대화형으로 사용:
```bash
python main.py
```

### 3. Python 코드에서 직접 사용

```python
from agent.graph import run_dart_workflow
from utils.data_store import SessionDataStore

# 데이터 저장소 초기화
data_store = SessionDataStore()

# 워크플로우 실행
result = run_dart_workflow(
    "삼성전자의 2023년 재무제표를 분석해줘",
    data_store
)
```

## 사용 예시

### 데이터 조회
- "삼성전자의 2023, 2024년 사업보고서 찾아줘"
- "LG전자의 최근 3년간 재무제표 데이터를 가져와줘"

### 데이터 분석
- "삼성전자와 LG전자의 매출액을 비교 분석해줘"
- "저장된 데이터로 매출 성장률을 계산해줘"
- "영업이익률 추이를 분석해줘"

## 프로젝트 구조

```
dart/
├── agent/                  # LangChain 에이전트 구현
│   ├── opendart_agent.py  # DART 데이터 수집 에이전트
│   ├── analyze_agent.py   # 데이터 분석 에이전트
│   └── graph.py          # LangGraph 워크플로우
├── streamlit/            # Streamlit UI
│   └── app.py           # 웹 애플리케이션
├── tools/                # 에이전트가 사용하는 도구들
│   └── opendart/        # OpenDart API 관련 도구
├── utils/               # 유틸리티 모듈
│   ├── data_store.py    # DataFrame 저장소
│   └── callbacks.py     # 처리 로그 콜백
├── resources/           # 설정 및 프롬프트
│   └── prompt/         # 에이전트별 프롬프트
└── tests/              # 테스트 코드
```

## 주요 컴포넌트

### 1. SessionDataStore
- DataFrame 형태의 재무 데이터를 중앙에서 관리
- 키-값 방식으로 데이터 저장 및 조회
- 세션별 독립적인 데이터 관리

### 2. OpendartAgent  
- OpenDart API를 활용한 재무제표 수집
- 자연어 쿼리를 API 호출로 변환
- 수집된 데이터를 SessionDataStore에 저장

### 3. AnalyzeAgent
- 저장된 DataFrame 데이터 분석
- 복잡한 계산 및 비교 분석 수행
- 시각화 및 인사이트 도출

### 4. LangGraph Workflow
- Planner가 사용자 요청을 분석하여 적절한 에이전트 선택
- 에이전트 간 상태 공유 및 협업
- Multi-turn 대화 지원

## 개발 로드맵

- [x] Phase 1: SessionDataStore 구현
- [x] Phase 2: OpendartAgent 구현  
- [x] Phase 3: AnalyzeAgent 구현
- [x] Phase 4: LangGraph 워크플로우 통합
- [x] Phase 5: Streamlit UI 구현
- [ ] Phase 6: 고급 분석 기능 추가
- [ ] Phase 7: 시각화 기능 강화

## 테스트

```bash
# 전체 테스트 실행
python -m pytest tests/

# 특정 테스트 실행
python -m pytest tests/test_workflow.py -v
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 
