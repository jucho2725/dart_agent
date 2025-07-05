"""
OpenDART 데이터 수집을 위한 LangChain 에이전트 모듈
"""

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from tools.opendart.langchain_tools import search_corp_code, search_financial_statements
from resources.config import OPENAI_API_KEY
from utils.data_store import SessionDataStore


def create_opendart_agent(data_store: SessionDataStore = None, verbose: bool = True):
    """
    OpenDART API 도구들을 사용하여 데이터 수집을 수행하는 AgentExecutor를 생성합니다.
    
    Args:
        data_store (SessionDataStore, optional): 세션 데이터 저장소. 
                                                 None인 경우 새로 생성됩니다.
        verbose (bool): 에이전트 실행 과정을 출력할지 여부. 기본값은 True.
    
    Returns:
        AgentExecutor: 설정된 OpendartAgent 실행기
    """
    
    # 1. 데이터 저장소 설정
    if data_store is None:
        data_store = SessionDataStore()
    
    # 2. 사용할 도구들을 리스트로 정의
    tools = [
        search_corp_code,
        search_financial_statements,
    ]
    
    # 3. 에이전트가 사용할 LLM 정의
    # 환경 변수에서 API 키 가져오기
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
    
    llm = ChatOpenAI(
        model="gpt-4", 
        temperature=0,
        api_key=OPENAI_API_KEY
    )
    
    # 4. 프롬프트 템플릿 설정
    # 에이전트에게 역할과 도구 사용법을 안내하는 지침
    system_prompt = """당신은 한국 기업의 재무 데이터를 전문적으로 수집하는 DART 데이터 분석 어시스턴트입니다.

주요 역할:
1. 사용자가 요청한 기업의 DART 고유번호(corp_code)를 검색합니다.
2. 기업의 재무제표 정보를 조회하고 제공합니다.
3. 정확하고 최신의 공시 데이터를 기반으로 답변합니다.

도구 사용 가이드:
- 먼저 search_corp_code 도구로 기업의 정확한 이름과 고유번호를 확인하세요.
- 재무제표 조회 시 연도를 명시하지 않으면 가장 최근 연도(2023년)를 기본으로 사용합니다.
- 사용자가 "작년", "올해" 등의 표현을 사용하면 적절한 연도로 변환하세요.

응답 원칙:
- 한국어로 친절하고 전문적으로 응답합니다.
- 숫자는 읽기 쉽게 한국 단위(억원, 조원)로 표시합니다.
- 재무 데이터는 정확성을 최우선으로 합니다.
"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    
    # 5. LLM, 도구, 프롬프트를 결합하여 에이전트 생성
    agent = create_openai_tools_agent(llm, tools, prompt)
    
    # 6. 에이전트 실행기 생성
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=verbose,
        handle_parsing_errors=True,
        max_iterations=5  # 무한 루프 방지
    )
    
    # 데이터 저장소는 별도로 반환하거나 다른 방식으로 관리
    # agent_executor.data_store = data_store  # 이 부분 제거
    
    return agent_executor


def test_opendart_agent():
    """OpendartAgent 테스트 함수"""
    print("=== OpendartAgent 테스트 시작 ===\n")
    
    try:
        # 에이전트 생성
        agent = create_opendart_agent()
        
        # 테스트 케이스 1: 기업 고유번호 검색
        print("테스트 1: 카카오의 DART 고유번호 검색")
        print("-" * 50)
        result1 = agent.invoke({"input": "카카오의 DART 고유번호는 뭐야?"})
        print(f"결과: {result1['output']}\n")
        
        # 테스트 케이스 2: 재무제표 검색
        print("테스트 2: 삼성전자 2023년 재무제표 검색")
        print("-" * 50)
        result2 = agent.invoke({"input": "삼성전자 2023년 재무제표 검색해줘"})
        print(f"결과: {result2['output']}\n")
        
        print("=== 테스트 완료 ===")
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 직접 실행 시 테스트 실행
    test_opendart_agent() 
