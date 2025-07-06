"""
처리 과정 로깅을 위한 콜백 핸들러
"""

from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.agents import AgentAction, AgentFinish
from typing import Any, Dict, List, Optional
import datetime
import json


class SimpleToolCallbackHandler(BaseCallbackHandler):
    """도구 사용 정보만 간단히 출력하는 콜백 핸들러 (verbose=False 모드용)"""
    
    def __init__(self):
        super().__init__()
        
    def on_tool_start(self, serialized: Optional[Dict[str, Any]], input_str: str, **kwargs: Any) -> Any:
        """도구 실행 시작 시 간단한 정보만 출력"""
        try:
            # serialized가 None인 경우 처리
            if serialized is None:
                tool_name = "Unknown Tool"
            else:
                tool_name = serialized.get("name", serialized.get("_type", "Unknown Tool"))
            
            # 입력값 요약 (너무 길면 축약)
            if len(input_str) > 100:
                input_summary = input_str[:100] + "..."
            else:
                input_summary = input_str
                
            print(f"\n🔧 도구 사용: {tool_name}")
            print(f"   입력: {input_summary}")
        except Exception as e:
            # 오류 발생 시 무시하고 계속 진행
            pass
            
    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        """도구 실행 완료 시 성공 표시만"""
        try:
            print(f"   ✓ 완료")
        except Exception as e:
            pass


class StreamlitLogCallbackHandler(BaseCallbackHandler):
    """AI의 처리 과정을 실시간으로 수집하여 Streamlit에 표시하기 위한 콜백 핸들러"""
    
    def __init__(self, agent_name: str = "Unknown Agent"):
        super().__init__()
        self.logs = []
        self.agent_name = agent_name
        self.current_action = None
        
    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        """에이전트가 어떤 도구를 어떤 입력으로 사용하는지 기록합니다."""
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            
            # 에이전트 행동을 구조화된 형태로 저장
            action_data = {
                "timestamp": timestamp,
                "agent": self.agent_name,
                "action_type": "tool_use",
                "tool": action.tool,
                "tool_input": action.tool_input,
                "log": action.log
            }
            
            # JSON 형식으로 변환
            self.current_action = action_data
            self.logs.append(json.dumps(action_data, ensure_ascii=False, indent=2))
            
        except Exception as e:
            # 오류 발생 시 무시하고 계속 진행
            pass
        
    def on_tool_start(self, serialized: Optional[Dict[str, Any]], input_str: str, **kwargs: Any) -> Any:
        """도구 실행 시작 시 로그 - 중복 방지를 위해 agent_action에서만 기록"""
        # 이미 agent_action에서 기록했으므로 여기서는 skip
        pass
        
    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        """도구 실행 완료 시 결과 추가"""
        try:
            if self.current_action:
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                
                # 도구 실행 결과를 구조화된 형태로 저장
                result_data = {
                    "timestamp": timestamp,
                    "agent": self.agent_name,
                    "action_type": "tool_result",
                    "tool": self.current_action.get("tool", "Unknown"),
                    "result": str(output)[:500] if output else "No output"  # 결과가 너무 길면 축약
                }
                
                self.logs.append(json.dumps(result_data, ensure_ascii=False, indent=2))
                self.current_action = None
                
        except Exception as e:
            # 오류 발생 시 무시하고 계속 진행
            pass
        
    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        """에이전트가 최종 응답을 생성할 때 기록"""
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            
            # 최종 응답을 구조화된 형태로 저장
            finish_data = {
                "timestamp": timestamp,
                "agent": self.agent_name,
                "action_type": "final_answer",
                "output": str(finish.return_values.get("output", ""))[:500]  # 너무 길면 축약
            }
            
            self.logs.append(json.dumps(finish_data, ensure_ascii=False, indent=2))
            
        except Exception as e:
            # 오류 발생 시 무시하고 계속 진행
            pass
        
    def on_llm_start(self, serialized: Optional[Dict[str, Any]], prompts: List[str], **kwargs: Any) -> Any:
        """LLM 호출 시작 - 주요 결정 사항만 기록"""
        # 너무 많은 로그를 방지하기 위해 skip
        pass
        
    def on_llm_end(self, response, **kwargs: Any) -> Any:
        """LLM 호출 완료 - 주요 결정 사항만 기록"""
        # 너무 많은 로그를 방지하기 위해 skip
        pass
        
    def on_chain_start(self, serialized: Optional[Dict[str, Any]], inputs: Optional[Dict[str, Any]], **kwargs: Any) -> Any:
        """체인 실행 시작 - 의미없는 로그이므로 skip"""
        pass
        
    def on_chain_end(self, outputs: Optional[Dict[str, Any]], **kwargs: Any) -> Any:
        """체인 실행 완료 - 의미없는 로그이므로 skip"""
        pass
        
    def clear_logs(self):
        """로그 초기화"""
        self.logs = []
        self.current_action = None
        
    def get_logs(self) -> List[str]:
        """수집된 로그 반환"""
        return self.logs 
