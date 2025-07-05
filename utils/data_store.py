from typing import Dict, Any, List
import pandas as pd

class SessionDataStore:
    """
    대화 세션 동안 수집된 모든 데이터를 저장하고 관리하는 클래스.
    주로 DataFrame 형태의 데이터를 저장하며, 고유한 key를 통해 접근합니다.
    """

    def __init__(self):
        """데이터를 저장할 내부 딕셔너리를 초기화합니다."""
        self._data: Dict[str, Any] = {}

    def add(self, key: str, data: pd.DataFrame):
        """
        주어진 key로 데이터를 저장소에 추가합니다.
        
        Args:
            key (str): 데이터를 식별할 고유한 키.
            data (pd.DataFrame): 저장할 DataFrame 객체.
        """
        if not isinstance(key, str) or not key:
            raise ValueError("Key는 비어있지 않은 문자열이어야 합니다.")
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data는 Pandas DataFrame이어야 합니다.")
            
        print(f"데이터 추가됨: {key}")
        self._data[key] = data

    def get(self, key: str) -> pd.DataFrame:
        """
        주어진 key에 해당하는 데이터를 반환합니다.
        
        Args:
            key (str): 조회할 데이터의 키.
            
        Returns:
            pd.DataFrame: 조회된 DataFrame 객체.
            
        Raises:
            KeyError: 해당 key의 데이터가 존재하지 않을 경우 발생.
        """
        if key not in self._data:
            raise KeyError(f"'{key}'에 해당하는 데이터를 찾을 수 없습니다.")
        return self._data[key]

    def list_keys(self) -> List[str]:
        """
        저장소에 있는 모든 데이터의 key 리스트를 반환합니다.
        이 리스트는 PlannerAgent가 사용 가능한 데이터를 인지하는 데 사용됩니다.
        
        Returns:
            List[str]: 모든 데이터 키의 리스트.
        """
        return list(self._data.keys()) 
