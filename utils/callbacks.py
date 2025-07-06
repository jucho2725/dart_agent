"""
처리 과정 로깅을 위한 콜백 핸들러
"""

from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.agents import AgentAction
from typing import Any, Dict, List, Optional
import datetime


class StreamlitLogCallbackHandler(BaseCallbackHandler):
    """AI의 처리 과정을 실시간으로 수집하여 Streamlit에 표시하기 위한 콜백 핸들러"""
    
    def __init__(self):
        super().__init__()
        self.logs = []
        
    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        """에이전트가 어떤 도구를 어떤 입력으로 사용하는지 기록합니다."""
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            
            # 입력값 포맷팅 (너무 길면 축약)
            input_str = str(action.tool_input)
            if len(input_str) > 200:
                input_str = input_str[:200] + "..."
                
            log_entry = f"**[{timestamp}] Agent Action**:\n- **Tool**: `{action.tool}`\n- **Input**: `{input_str}`"
            self.logs.append(log_entry)
        except Exception as e:
            # 오류 발생 시 무시하고 계속 진행
            pass
        
    def on_tool_start(self, serialized: Optional[Dict[str, Any]], input_str: str, **kwargs: Any) -> Any:
        """도구 실행 시작 시 로그"""
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            
            # serialized가 None인 경우 처리
            if serialized is None:
                tool_name = "Unknown Tool"
            else:
                tool_name = serialized.get("name", serialized.get("_type", "Unknown Tool"))
            
            # 입력값 포맷팅
            if len(input_str) > 200:
                input_str = input_str[:200] + "..."
                
            log_entry = f"**[{timestamp}] Tool Started**:\n- **Tool**: `{tool_name}`\n- **Input**: `{input_str}`"
            self.logs.append(log_entry)
        except Exception as e:
            # 오류 발생 시 무시하고 계속 진행
            pass
        
    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        """도구 실행 완료 시 로그"""
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            
            # 출력값 포맷팅
            output_str = str(output) if output else "No output"
            if len(output_str) > 200:
                output_str = output_str[:200] + "..."
                
            log_entry = f"**[{timestamp}] Tool Completed**:\n- **Output**: `{output_str}`"
            self.logs.append(log_entry)
        except Exception as e:
            # 오류 발생 시 무시하고 계속 진행
            pass
        
    def on_llm_start(self, serialized: Optional[Dict[str, Any]], prompts: List[str], **kwargs: Any) -> Any:
        """LLM 호출 시작 시 로그"""
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            
            # serialized가 None인 경우 처리
            if serialized is None:
                model_name = "Unknown Model"
            else:
                model_name = serialized.get("name", serialized.get("_type", "Unknown Model"))
            
            log_entry = f"**[{timestamp}] LLM Started**:\n- **Model**: `{model_name}`\n- **Prompt Count**: {len(prompts) if prompts else 0}"
            self.logs.append(log_entry)
        except Exception as e:
            # 오류 발생 시 무시하고 계속 진행
            pass
        
    def on_llm_end(self, response, **kwargs: Any) -> Any:
        """LLM 호출 완료 시 로그"""
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            
            # 응답 내용 요약
            content = "Response generated"
            if hasattr(response, "generations") and response.generations:
                if response.generations[0]:
                    content = response.generations[0][0].text if response.generations[0] else "No response"
                    if len(content) > 200:
                        content = content[:200] + "..."
                
            log_entry = f"**[{timestamp}] LLM Completed**:\n- **Response**: `{content}`"
            self.logs.append(log_entry)
        except Exception as e:
            # 오류 발생 시 무시하고 계속 진행
            pass
        
    def on_chain_start(self, serialized: Optional[Dict[str, Any]], inputs: Optional[Dict[str, Any]], **kwargs: Any) -> Any:
        """체인 실행 시작 시 로그"""
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            
            # serialized가 None인 경우 처리
            if serialized is None:
                chain_name = "Unknown Chain"
            else:
                chain_name = serialized.get("name", serialized.get("_type", "Unknown Chain"))
            
            log_entry = f"**[{timestamp}] Chain Started**:\n- **Chain**: `{chain_name}`"
            self.logs.append(log_entry)
        except Exception as e:
            # 오류 발생 시 무시하고 계속 진행
            pass
        
    def on_chain_end(self, outputs: Optional[Dict[str, Any]], **kwargs: Any) -> Any:
        """체인 실행 완료 시 로그"""
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            
            log_entry = f"**[{timestamp}] Chain Completed**"
            self.logs.append(log_entry)
        except Exception as e:
            # 오류 발생 시 무시하고 계속 진행
            pass
        
    def clear_logs(self):
        """로그 초기화"""
        self.logs = []
        
    def get_logs(self) -> List[str]:
        """수집된 로그 반환"""
        return self.logs 
