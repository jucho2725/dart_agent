"""
DART 데이터 분석 에이전트 Streamlit UI
"""

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.graph import create_dart_workflow
from utils.data_store import SessionDataStore
from utils.callbacks import StreamlitLogCallbackHandler


# --- 페이지 설정 ---
st.set_page_config(
    page_title="DART 데이터 분석 에이전트",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 타이틀 및 설명 ---
st.title("DART 데이터 분석 에이전트 🤖")
st.markdown(
    """
    안녕하세요! DART 공시 정보를 조회하고 분석할 수 있는 AI 에이전트입니다.
    
    **사용 예시:**
    - "삼성전자의 2023, 2024년 사업보고서 찾아줘"
    - "삼성전자와 LG전자의 최근 3년간 매출액을 비교해줘"
    - "저장된 데이터로 매출액 성장률을 계산해줘"
    """
)

# 구분선
st.divider()

# --- 세션 상태 초기화 ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        AIMessage(content="안녕하세요! DART 공시 정보에 대해 무엇이든 물어보세요. 예를 들어:\n\n"
                         "- 특정 기업의 재무제표를 조회하거나\n"
                         "- 여러 기업의 재무 데이터를 비교 분석할 수 있습니다.")
    ]

if "data_store" not in st.session_state:
    st.session_state.data_store = SessionDataStore()
    
if "graph_app" not in st.session_state:
    st.session_state.graph_app = create_dart_workflow()

# --- 사이드바 - 저장된 데이터 표시 ---
with st.sidebar:
    st.header("📊 저장된 데이터")
    
    if st.session_state.data_store.list_keys():
        st.write("**현재 저장된 데이터:**")
        for key in st.session_state.data_store.list_keys():
            st.write(f"- `{key}`")
            
        # 데이터 미리보기 기능
        selected_key = st.selectbox(
            "데이터 미리보기",
            options=["선택하세요"] + st.session_state.data_store.list_keys()
        )
        
        if selected_key != "선택하세요":
            df = st.session_state.data_store.get_dataframe(selected_key)
            if df is not None:
                st.write(f"**{selected_key}** (행: {len(df)}, 열: {len(df.columns)})")
                st.dataframe(df.head(5), use_container_width=True)
    else:
        st.info("아직 저장된 데이터가 없습니다.")
    
    # 세션 리셋 버튼
    st.divider()
    if st.button("🔄 새 대화 시작", type="secondary", use_container_width=True):
        st.session_state.messages = [
            AIMessage(content="안녕하세요! DART 공시 정보에 대해 무엇이든 물어보세요.")
        ]
        st.session_state.data_store = SessionDataStore()
        st.session_state.graph_app = create_dart_workflow()
        st.rerun()

# --- 대화 기록 표시 ---
messages_container = st.container()
with messages_container:
    for message in st.session_state.messages:
        # 플래너 결정 메시지는 표시하지 않음
        if isinstance(message, AIMessage) and message.content.startswith("플래너 결정:"):
            continue
            
        with st.chat_message(message.type):
            st.markdown(message.content)

# --- 사용자 입력 처리 ---
if prompt := st.chat_input("여기에 질문을 입력하세요..."):
    # 사용자 메시지 추가 및 표시
    st.session_state.messages.append(HumanMessage(content=prompt))
    
    with messages_container:
        with st.chat_message("human"):
            st.markdown(prompt)
    
    # AI 응답 생성
    with messages_container:
        with st.chat_message("ai"):
            # 로그 콜백 핸들러 생성
            log_callback = StreamlitLogCallbackHandler()
            config = {"callbacks": [log_callback], "recursion_limit": 50}
            
            # 응답 생성 중 표시
            with st.spinner("분석 중입니다..."):
                try:
                    # 상태 구성
                    state_input = {
                        "messages": st.session_state.messages,
                        "data_store": st.session_state.data_store,
                        "target_df_key": "",
                        "next_agent": ""
                    }
                    
                    # 워크플로우 실행
                    final_state = st.session_state.graph_app.invoke(state_input, config=config)
                    
                    # 최종 응답 추출 (플래너 결정 메시지 제외)
                    response_messages = []
                    for msg in final_state["messages"]:
                        if (isinstance(msg, AIMessage) and 
                            not msg.content.startswith("플래너 결정:") and
                            msg not in st.session_state.messages):
                            response_messages.append(msg)
                    
                    # 응답이 있는 경우 표시
                    if response_messages:
                        # 가장 마지막 응답 메시지 표시
                        response_message = response_messages[-1]
                        st.markdown(response_message.content)
                        
                        # 세션 상태 업데이트
                        st.session_state.messages.append(response_message)
                        
                        # 데이터 저장소 업데이트
                        st.session_state.data_store = final_state["data_store"]
                    else:
                        # 응답이 없는 경우 (이미 처리된 요청)
                        fallback_message = AIMessage(
                            content="이미 요청하신 내용에 대해 답변드렸습니다. 추가로 궁금하신 사항이 있으시면 말씀해주세요!"
                        )
                        st.markdown(fallback_message.content)
                        st.session_state.messages.append(fallback_message)
                    
                except Exception as e:
                    error_message = f"처리 중 오류가 발생했습니다: {str(e)}"
                    st.error(error_message)
                    st.session_state.messages.append(AIMessage(content=error_message))
            
            # 처리 과정 로그 표시
            with st.expander("🔍 처리 과정 상세보기", expanded=False):
                if log_callback.logs:
                    for log in log_callback.logs:
                        st.markdown(log, unsafe_allow_html=True)
                        st.markdown("---")  # 구분선
                else:
                    st.info("이번 요청에서는 처리 과정 로그가 기록되지 않았습니다.")
                    st.caption("(콜백 핸들러가 실행되었지만 로그가 캡처되지 않음)")
            
    # 사이드바 업데이트를 위해 페이지 새로고침
    st.rerun()

# --- 하단 정보 ---
st.divider()
st.caption(
    "💡 **팁**: 먼저 기업의 재무제표를 조회한 후, 저장된 데이터를 활용하여 분석을 요청하세요. "
    "사이드바에서 현재 저장된 데이터를 확인할 수 있습니다."
) 
