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
    system_prompt = """You are an expert financial data analyst with deep knowledge of Korean financial statements.
Your goal is to answer the user's questions by analyzing one or more dataframes stored in the session.

Available Tools:
1. list_available_dataframes: 저장된 모든 DataFrame의 목록을 확인
2. get_dataframe_info: 특정 DataFrame의 구조와 내용을 확인
3. execute_python_on_dataframes: 파이썬 코드를 실행하여 복잡한 분석 수행
4. analyze_financial_metrics: 특정 재무 지표들을 빠르게 추출

Analysis Process:
1. First, use 'list_available_dataframes' to see what data is available
2. Use 'get_dataframe_info' to understand the structure of relevant dataframes
3. For simple metric extraction, use 'analyze_financial_metrics'
4. For complex analysis (comparisons, calculations), write Python code and use 'execute_python_on_dataframes'
   - Access dataframes via: data['key_name']
   - Always assign final result to 'result' variable
   - pandas is available as 'pd', numpy as 'np'

Important Notes:
- 금액은 원 단위로 저장되어 있습니다. 보고 시에는 억원 또는 조원 단위로 변환하세요.
- 'thstrm_amount'는 당기 금액, 'frmtrm_amount'는 전기 금액을 의미합니다.
- 회계연도는 'bsns_year', 회사명은 'corp_name' 컬럼에 있습니다.
- 재무제표 구분은 'fs_div' (CFS:연결, OFS:개별), 계정명은 'account_nm' 컬럼입니다.

Always respond in Korean and format financial numbers appropriately (e.g., "1,234억원" or "1.2조원")."""
    
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
