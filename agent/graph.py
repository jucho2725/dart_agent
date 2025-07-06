"""
LangGraph를 사용한 DART 에이전트 워크플로우 구현
"""

from typing import TypedDict, Annotated, List, Literal, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from operator import add
from pydantic import SecretStr

from utils.data_store import SessionDataStore
from agent.opendart_agent import create_opendart_agent
from agent.analyze_agent import create_multi_df_analyze_agent
from resources.prompt_loader import prompt_loader
from resources.config import get_openai_api_key


# 1. 그래프의 상태 정의
class AgentState(TypedDict):
    """워크플로우 전체에서 공유되는 상태"""
    messages: Annotated[List[BaseMessage], add]
    data_store: SessionDataStore
    target_df_key: str  # AnalyzeAgent가 사용할 키
    next_agent: str  # 다음에 실행할 에이전트
    processing_logs: Annotated[List[str], add]  # 처리 과정 로그


# 2. 그래프 노드 및 라우팅 로직 구현
class DARTWorkflow:
    """DART 에이전트 워크플로우 관리 클래스"""
    
    def __init__(self, verbose: bool = False):
        """워크플로우 초기화
        
        Args:
            verbose (bool): 에이전트 실행 과정을 출력할지 여부. 기본값은 False.
        """
        # 프롬프트 로더 초기화
        self.prompt_loader = prompt_loader
        self.verbose = verbose
        
        # 플래너 LLM 설정
        api_key = get_openai_api_key()
        self.planner_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=SecretStr(api_key) if api_key else None
        )
        
        # 프롬프트 로드
        prompts = self.prompt_loader.load_agent_prompts("planner")
        self.planner_system_prompt = prompts["system"]
        self.planner_user_prompt = prompts["user"]
        
    def planner_node(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """
        사용자의 요청을 분석하고 적절한 에이전트로 라우팅하는 플래너 노드
        
        Args:
            state: 현재 워크플로우 상태
            config: 런타임 설정 (콜백 포함)
            
        Returns:
            업데이트된 상태
        """
        # 메시지 히스토리 포맷팅
        message_history = "\n".join([
            f"{msg.type}: {msg.content[:200]}..."  # 내용이 너무 길면 자르기
            for msg in state["messages"][-10:]  # 최근 10개 메시지만 사용
        ])
        
        # 사용 가능한 데이터 키 가져오기
        available_keys = state["data_store"].list_keys() if state.get("data_store") else []
        available_keys_str = ", ".join(available_keys) if available_keys else "No data available"
        
        # 최신 사용자 메시지 가져오기
        latest_message = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                latest_message = msg.content
                break
        
        # 이전 AI 응답 확인 - 이미 처리된 요청인지 확인
        last_ai_response = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and isinstance(msg.content, str) and not msg.content.startswith("플래너 결정:"):
                last_ai_response = msg.content[:500]  # 최근 AI 응답의 일부
                break
        
        # 이미 처리된 요청인지 확인
        # 현재 사용자 요청이 이전 응답에서 완전히 처리되었는지 확인
        if last_ai_response and latest_message and isinstance(latest_message, str):
            # 데이터 수집이 완료되고 추가 질문이 없는 경우에만 END
            if ("조회하여" in last_ai_response and "저장했습니다" in last_ai_response
                and "추가로 궁금한 사항" in last_ai_response
                and not any(keyword in latest_message.lower() for keyword in ["분석", "비교", "계산", "얼마", "조회"])):
                # 이미 처리된 요청이므로 END로 라우팅
                state["messages"].append(AIMessage(content="플래너 결정: END"))
                state["next_agent"] = "END"
                return state
        
        # 프롬프트 구성
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.planner_system_prompt),
            ("user", self.planner_user_prompt)
        ])
        
        # LLM 호출 - config 전달
        response = self.planner_llm.invoke(
            prompt.format_messages(
                messages=message_history,
                available_data_keys=available_keys_str,
                input=latest_message
            ),
            config=config
        )
        
        # 결정 파싱
        decision = response.content.strip() if isinstance(response.content, str) else str(response.content).strip()
        
        # 결정 검증
        valid_decisions = ["OpendartAgent", "AnalyzeAgent", "END"]
        if decision not in valid_decisions:
            print(f"경고: 잘못된 결정 '{decision}'. 기본값 'END'로 설정합니다.")
            decision = "END"
        
        # 상태 업데이트
        state["messages"].append(AIMessage(content=f"플래너 결정: {decision}"))
        state["next_agent"] = decision
        
        return state
    
    def opendart_node(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """
        OpendartAgent를 실행하는 노드
        
        Args:
            state: 현재 워크플로우 상태
            config: 런타임 설정 (콜백 포함)
            
        Returns:
            업데이트된 상태
        """
        from utils.callbacks import StreamlitLogCallbackHandler
        
        # 데이터 저장소 초기화 (필요한 경우)
        if not state.get("data_store"):
            state["data_store"] = SessionDataStore()
        
        # OpendartAgent 전용 콜백 핸들러 생성
        opendart_callback = StreamlitLogCallbackHandler(agent_name="OpendartAgent")
        
        # config에서 콜백 추출
        callbacks = config.get("callbacks", []) if config else []
        
        # callbacks가 리스트인지 확인하고 처리
        if isinstance(callbacks, list):
            agent_callbacks = callbacks + [opendart_callback]
        else:
            # CallbackManager인 경우
            agent_callbacks = [opendart_callback]
        
        # OpendartAgent 생성
        opendart_agent = create_opendart_agent(
            data_store=state["data_store"],
            verbose=self.verbose,
            callbacks=agent_callbacks
        )
        
        # 최신 사용자 메시지 가져오기
        latest_message = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                latest_message = msg.content
                break
        
        # 에이전트 실행
        agent_config = {**config, "callbacks": agent_callbacks}
        result = opendart_agent.invoke(
            {"input": latest_message}, 
            config=RunnableConfig(**agent_config)
        )
        
        # 결과를 메시지에 추가
        state["messages"].append(AIMessage(content=result["output"]))
        
        # 에이전트 로그를 상태에 추가
        if "processing_logs" not in state:
            state["processing_logs"] = []
        state["processing_logs"].extend(opendart_callback.logs)
        
        # 🔍 디버그: 로그 추가 확인
        print(f"🔍 [DEBUG] opendart_node: Added {len(opendart_callback.logs)} logs to state")
        print(f"🔍 [DEBUG] Total processing_logs in state: {len(state['processing_logs'])}")
        
        return state
    
    def analyze_node(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """
        AnalyzeAgent를 실행하는 노드
        
        Args:
            state: 현재 워크플로우 상태
            config: 런타임 설정 (콜백 포함)
            
        Returns:
            업데이트된 상태
        """
        from utils.callbacks import StreamlitLogCallbackHandler
        
        # 데이터 저장소 확인
        if not state.get("data_store"):
            state["messages"].append(
                AIMessage(content="분석할 데이터가 없습니다. 먼저 데이터를 수집해주세요.")
            )
            return state
        
        # AnalyzeAgent 전용 콜백 핸들러 생성
        analyze_callback = StreamlitLogCallbackHandler(agent_name="AnalyzeAgent")
        
        # config에서 콜백 추출
        callbacks = config.get("callbacks", []) if config else []
        
        # callbacks가 리스트인지 확인하고 처리
        if isinstance(callbacks, list):
            agent_callbacks = callbacks + [analyze_callback]
        else:
            # CallbackManager인 경우
            agent_callbacks = [analyze_callback]
        
        # AnalyzeAgent 생성
        analyze_agent = create_multi_df_analyze_agent(
            data_store=state["data_store"],
            model="gpt-4o-mini",
            verbose=self.verbose,
            callbacks=agent_callbacks
        )
        
        # 최신 사용자 메시지 가져오기
        latest_message = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                latest_message = msg.content
                break
        
        # 에이전트 실행
        agent_config = {**config, "callbacks": agent_callbacks}
        result = analyze_agent.invoke(
            {"input": latest_message},
            config=RunnableConfig(**agent_config)
        )
        
        # 결과를 메시지에 추가
        state["messages"].append(AIMessage(content=result["output"]))
        
        # 에이전트 로그를 상태에 추가
        if "processing_logs" not in state:
            state["processing_logs"] = []
        state["processing_logs"].extend(analyze_callback.logs)
        
        # 🔍 디버그: 로그 추가 확인
        print(f"🔍 [DEBUG] analyze_node: Added {len(analyze_callback.logs)} logs to state")
        print(f"🔍 [DEBUG] Total processing_logs in state: {len(state['processing_logs'])}")
        
        return state
    
    def router_logic(self, state: AgentState) -> Literal["opendart", "analyze", "end"]:
        """
        플래너의 결정에 따라 다음 노드를 선택하는 라우터
        
        Args:
            state: 현재 워크플로우 상태
            
        Returns:
            다음 노드 이름
        """
        next_agent = state.get("next_agent", "END")
        
        if next_agent == "OpendartAgent":
            return "opendart"
        elif next_agent == "AnalyzeAgent":
            return "analyze"
        else:
            return "end"


# 3. 그래프 구성 및 컴파일
def create_dart_workflow(verbose: bool = False):
    """DART 워크플로우 그래프를 생성하고 컴파일합니다.
    
    Args:
        verbose (bool): 에이전트 실행 과정을 출력할지 여부. 기본값은 False.
    """
    
    # 워크플로우 매니저 생성
    workflow_manager = DARTWorkflow(verbose=verbose)
    
    # 그래프 생성
    graph = StateGraph(AgentState)
    
    # 노드 추가
    graph.add_node("planner", workflow_manager.planner_node)
    graph.add_node("opendart", workflow_manager.opendart_node)
    graph.add_node("analyze", workflow_manager.analyze_node)
    
    # 엔트리 포인트 설정
    graph.set_entry_point("planner")
    
    # 조건부 엣지 추가
    graph.add_conditional_edges(
        "planner",
        workflow_manager.router_logic,
        {
            "opendart": "opendart",
            "analyze": "analyze",
            "end": END
        }
    )
    
    # 에이전트 실행 후 다시 플래너로
    graph.add_edge("opendart", "planner")
    graph.add_edge("analyze", "planner")
    
    # 그래프 컴파일
    app = graph.compile()
    
    return app


# 편의 함수
def run_dart_workflow(user_input: str, data_store: SessionDataStore = None, verbose: bool = False):
    """
    DART 워크플로우를 실행하는 편의 함수
    
    Args:
        user_input: 사용자 입력
        data_store: 기존 데이터 저장소 (선택사항)
        verbose: 에이전트 실행 과정을 출력할지 여부. 기본값은 False.
        
    Returns:
        최종 상태
    """
    from utils.callbacks import SimpleToolCallbackHandler
    
    app = create_dart_workflow(verbose=verbose)
    
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "data_store": data_store if data_store is not None else SessionDataStore(),
        "target_df_key": "",
        "next_agent": "",
        "processing_logs": []  # 초기 상태에 로그 필드 추가
    }
    
    # 재귀 제한 및 콜백 설정
    config = {"recursion_limit": 50}
    
    # verbose=False일 때 간단한 툴 콜백 추가
    if not verbose:
        config["callbacks"] = [SimpleToolCallbackHandler()]
    
    result = app.invoke(initial_state, config=config)
    
    return result 
