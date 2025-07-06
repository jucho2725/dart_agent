"""
Multi-DataFrame 분석 에이전트
여러 DataFrame을 동시에 분석할 수 있는 고급 분석 기능을 제공합니다.
"""

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from typing import Optional, Dict, Any

from utils.data_store import SessionDataStore
from tools import analysis_tools
from resources.config import get_openai_api_key


def create_multi_df_analyze_agent(
    data_store: SessionDataStore,
    model: str = "gpt-4o-mini",
    temperature: float = 0
) -> AgentExecutor:
    """
    SessionDataStore 전체를 컨텍스트로 사용하여 여러 데이터프레임을
    종합적으로 분석하는 커스텀 에이전트를 생성합니다.
    
    Args:
        data_store (SessionDataStore): 분석할 데이터들이 저장된 데이터 저장소
        model (str): 사용할 OpenAI 모델명 (기본값: "gpt-4o-mini")
        temperature (float): LLM의 temperature 설정 (0: 결정적, 1: 창의적)
        
    Returns:
        AgentExecutor: 설정된 분석 에이전트
        
    Examples:
        >>> store = SessionDataStore()
        >>> # store에 데이터 추가...
        >>> agent = create_multi_df_analyze_agent(store)
        >>> result = agent.invoke({"input": "2023년과 2024년 매출액 비교해줘"})
    """
    # 1. 데이터 저장소를 전역 변수로 설정
    analysis_tools.set_data_store(data_store)
    
    # 2. 사용할 도구들 준비
    tools = [
        analysis_tools.list_available_dataframes,
        analysis_tools.get_dataframe_info,
        analysis_tools.execute_python_on_dataframes,
        analysis_tools.analyze_financial_metrics,
    ]
    
    # 3. LLM 초기화
    api_key = get_openai_api_key()
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key
    )
    
    # 4. 시스템 프롬프트 정의
    system_prompt = """당신은 한국 기업의 재무 데이터를 전문적으로 분석하는 재무 분석 전문가입니다.

주요 역할:
1. SessionDataStore에 저장된 여러 DataFrame을 동시에 분석합니다.
2. 연도별 비교, 회사 간 비교 등 복잡한 분석을 수행합니다.
3. 재무비율 계산, 성장률 분석 등 심층적인 인사이트를 제공합니다.

도구 사용 가이드:
- 먼저 list_available_dataframes로 사용 가능한 데이터를 확인하세요.
- get_dataframe_info로 각 DataFrame의 구조를 파악하세요.
- analyze_financial_metrics로 재무 지표를 추출하고 분석하세요.
- execute_python_on_dataframes로 복잡한 계산을 수행하세요.

계정명 처리:
- 회사나 연도별로 계정명이 다를 수 있습니다 (예: '매출액' vs '영업수익').
- analyze_financial_metrics가 'substituted': True를 반환하면, 요청한 계정명 대신 유사한 계정명을 사용했다는 의미입니다.
- 이 경우 반드시 "요청하신 '{{requested_account_name}}' 대신 '{{actual_account_name}}'을 사용하여 분석했습니다"와 같이 설명하세요.

응답 원칙:
- 한국어로 전문적이고 정확하게 응답합니다.
- 숫자는 읽기 쉽게 단위를 표시합니다 (억원, 조원).
- 성장률, 비율 등은 소수점 1자리까지 표시합니다.
- 분석 결과에 대한 해석과 인사이트를 포함합니다.
- 대체 계정명을 사용한 경우 반드시 명시합니다.
"""
    
    # 5. 프롬프트 템플릿 생성
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # 6. 에이전트 생성
    agent = create_openai_tools_agent(llm, tools, prompt)
    
    # 7. AgentExecutor 생성
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10  # 복잡한 분석을 위해 충분한 반복 허용
    )
    
    return agent_executor


def create_comparison_analysis_agent(
    data_store: SessionDataStore,
    model: str = "gpt-4o-mini"
) -> AgentExecutor:
    """
    재무제표 비교 분석에 특화된 에이전트를 생성합니다.
    
    주로 연도별, 회사별 비교 분석에 최적화되어 있습니다.
    
    Args:
        data_store (SessionDataStore): 분석할 데이터들이 저장된 데이터 저장소
        model (str): 사용할 OpenAI 모델명
        
    Returns:
        AgentExecutor: 비교 분석 전문 에이전트
    """
    # 기본 에이전트에 비교 분석 특화 프롬프트 추가
    agent = create_multi_df_analyze_agent(data_store, model)
    
    # 추가 설정이 필요한 경우 여기에 구현
    
    return agent 
