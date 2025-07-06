"""
프롬프트 파일 로더 유틸리티
프롬프트를 텍스트 파일에서 읽어오는 기능을 제공합니다.
"""

import os
from typing import Dict, Optional


class PromptLoader:
    """프롬프트 파일을 로드하고 관리하는 클래스"""
    
    def __init__(self, base_path: str = "resources/prompt"):
        """
        Args:
            base_path (str): 프롬프트 파일들이 저장된 기본 경로
        """
        self.base_path = base_path
    
    def load_prompt(self, agent_name: str, prompt_type: str = "system") -> str:
        """
        특정 에이전트의 프롬프트를 파일에서 읽어옵니다.
        
        Args:
            agent_name (str): 에이전트 이름 (예: "planner", "opendart", "analyze")
            prompt_type (str): 프롬프트 타입 ("system" 또는 "user")
            
        Returns:
            str: 프롬프트 텍스트
            
        Raises:
            FileNotFoundError: 프롬프트 파일이 존재하지 않을 경우
        """
        file_path = os.path.join(self.base_path, agent_name, f"{prompt_type}.txt")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    
    def load_agent_prompts(self, agent_name: str) -> Dict[str, str]:
        """
        특정 에이전트의 모든 프롬프트를 로드합니다.
        
        Args:
            agent_name (str): 에이전트 이름
            
        Returns:
            Dict[str, str]: {"system": "...", "user": "..."} 형태의 딕셔너리
        """
        prompts = {}
        
        # system 프롬프트 로드
        try:
            prompts["system"] = self.load_prompt(agent_name, "system")
        except FileNotFoundError:
            prompts["system"] = ""
        
        # user 프롬프트 로드
        try:
            prompts["user"] = self.load_prompt(agent_name, "user")
        except FileNotFoundError:
            prompts["user"] = "{input}"  # 기본값
        
        return prompts
    
    def reload_prompt(self, agent_name: str, prompt_type: str = "system") -> str:
        """
        프롬프트를 다시 로드합니다. (파일이 수정된 경우)
        
        Args:
            agent_name (str): 에이전트 이름
            prompt_type (str): 프롬프트 타입
            
        Returns:
            str: 프롬프트 텍스트
        """
        return self.load_prompt(agent_name, prompt_type)


# 싱글톤 인스턴스
prompt_loader = PromptLoader() 
