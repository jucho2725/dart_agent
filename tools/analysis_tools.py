"""
Multi-DataFrame 분석을 위한 LangChain 도구들
"""

from langchain.tools import tool
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import json

from utils.data_store import SessionDataStore


# 전역 데이터 저장소 (에이전트 생성 시 설정됨)
_global_data_store: Optional[SessionDataStore] = None


def set_data_store(data_store: SessionDataStore):
    """분석 도구들이 사용할 데이터 저장소를 설정합니다."""
    global _global_data_store
    _global_data_store = data_store


@tool
def list_available_dataframes() -> List[str]:
    """
    현재 SessionDataStore에 저장된 모든 데이터프레임의 키(이름) 목록을 반환합니다.
    
    분석을 시작하기 전에 어떤 데이터를 사용할 수 있는지 확인하기 위해 가장 먼저 사용해야 합니다.
    
    Returns:
        List[str]: 저장된 DataFrame들의 키 목록
        
    Examples:
        - 저장된 데이터 확인: list_available_dataframes()
        - 결과 예시: ['samsung_fs_2023_consolidated', 'samsung_fs_2024_consolidated']
    """
    if _global_data_store is None:
        return []
    return _global_data_store.list_keys()


@tool  
def get_dataframe_info(df_key: str) -> str:
    """
    지정한 키(df_key)에 해당하는 데이터프레임의 기본 정보를 반환합니다.
    
    데이터의 구조를 파악할 때 사용합니다. Shape, 컬럼 목록, 데이터 타입, 
    그리고 상위 5개 행을 포함한 상세 정보를 제공합니다.
    
    Args:
        df_key (str): 조회할 DataFrame의 키
        
    Returns:
        str: DataFrame의 상세 정보
        
    Examples:
        - 삼성전자 2023년 데이터 구조 확인: get_dataframe_info("samsung_fs_2023_consolidated")
    """
    if _global_data_store is None:
        return "데이터 저장소가 초기화되지 않았습니다."
        
    try:
        df = _global_data_store.get(df_key)
        
        info_parts = [
            f"=== DataFrame: {df_key} ===",
            f"Shape: {df.shape} (행: {df.shape[0]}, 열: {df.shape[1]})",
            f"\nColumns ({len(df.columns)}개):",
            ", ".join(df.columns.tolist()),
            f"\nData Types:",
        ]
        
        # 데이터 타입 정보
        for col, dtype in df.dtypes.items():
            info_parts.append(f"  - {col}: {dtype}")
        
        # 주요 컬럼 확인
        if 'account_nm' in df.columns and 'thstrm_amount' in df.columns:
            info_parts.append("\n주요 계정 항목 (상위 10개):")
            key_accounts = df[df['thstrm_amount'].notna()].nlargest(10, 'thstrm_amount')[['account_nm', 'thstrm_amount']]
            for _, row in key_accounts.iterrows():
                amount_in_100m = row['thstrm_amount'] / 100_000_000
                info_parts.append(f"  - {row['account_nm']}: {amount_in_100m:,.0f}억원")
        
        # 상위 5개 행
        info_parts.append(f"\n상위 5개 행:")
        info_parts.append(df.head().to_string())
        
        return "\n".join(info_parts)
        
    except KeyError:
        return f"'{df_key}' 키를 가진 DataFrame을 찾을 수 없습니다."
    except Exception as e:
        return f"오류 발생: {str(e)}"


@tool
def execute_python_on_dataframes(code: str) -> Dict[str, Any]:
    """
    SessionDataStore의 모든 데이터에 접근하여 파이썬 코드를 실행합니다.
    
    코드 내에서 'data' 딕셔너리를 통해 모든 DataFrame에 접근할 수 있습니다.
    예: data['samsung_fs_2023_consolidated']
    
    추가로 pandas(pd)와 numpy(np)가 미리 import되어 있습니다.
    
    Args:
        code (str): 실행할 파이썬 코드. 반드시 'result' 변수에 최종 결과를 할당해야 합니다.
        
    Returns:
        Dict[str, Any]: 실행 결과 또는 에러 메시지
        
    Examples:
        코드 예시:
        ```python
        # 2023년과 2024년 매출액 비교
        df_2023 = data['samsung_fs_2023_consolidated']
        df_2024 = data['samsung_fs_2024_consolidated']
        
        revenue_2023 = df_2023[df_2023['account_nm'].str.contains('매출액')]['thstrm_amount'].iloc[0]
        revenue_2024 = df_2024[df_2024['account_nm'].str.contains('매출액')]['thstrm_amount'].iloc[0]
        
        growth_rate = (revenue_2024 - revenue_2023) / revenue_2023 * 100
        result = f"매출액 성장률: {growth_rate:.1f}%"
        ```
    """
    if _global_data_store is None:
        return {"error": "데이터 저장소가 초기화되지 않았습니다."}
    
    try:
        # 실행 환경 준비
        namespace = {
            'data': _global_data_store._data,
            'pd': pd,
            'np': np,
            'result': None
        }
        
        # 코드 실행
        exec(code, namespace)
        
        # 결과 확인
        result = namespace.get('result')
        if result is None:
            return {"error": "코드 실행은 성공했지만 'result' 변수가 설정되지 않았습니다."}
        
        # 결과를 문자열로 변환
        if isinstance(result, pd.DataFrame):
            result_str = f"DataFrame 결과 (shape: {result.shape}):\n{result.to_string()}"
        elif isinstance(result, pd.Series):
            result_str = f"Series 결과:\n{result.to_string()}"
        else:
            result_str = str(result)
            
        return {"result": result_str}
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return {"error": f"코드 실행 중 오류 발생:\n{str(e)}\n\n상세 정보:\n{error_detail}"}


@tool
def analyze_financial_metrics(df_key: str, metrics: List[str]) -> Dict[str, Any]:
    """
    지정된 DataFrame에서 특정 재무 지표들을 추출하여 분석합니다.
    
    Args:
        df_key (str): 분석할 DataFrame의 키
        metrics (List[str]): 추출할 재무 지표 목록 (예: ['자산총계', '부채총계', '매출액'])
        
    Returns:
        Dict[str, Any]: 각 지표별 값과 분석 결과
        
    Examples:
        - analyze_financial_metrics("samsung_fs_2023_consolidated", ["자산총계", "부채총계", "자본총계"])
    """
    if _global_data_store is None:
        return {"error": "데이터 저장소가 초기화되지 않았습니다."}
    
    try:
        df = _global_data_store.get(df_key)
        results = {}
        
        for metric in metrics:
            # 해당 계정명을 포함하는 행 찾기
            metric_rows = df[df['account_nm'].str.contains(metric, na=False)]
            
            if not metric_rows.empty and 'thstrm_amount' in metric_rows.columns:
                # 가장 첫 번째 매칭되는 값 사용
                amount = metric_rows['thstrm_amount'].iloc[0]
                if pd.notna(amount):
                    amount_in_100m = amount / 100_000_000  # 억원 단위
                    if amount_in_100m >= 10000:
                        amount_in_t = amount_in_100m / 10000  # 조원 단위
                        results[metric] = {
                            "value": float(amount),
                            "formatted": f"{amount_in_t:,.1f}조원",
                            "unit": "조원"
                        }
                    else:
                        results[metric] = {
                            "value": float(amount),
                            "formatted": f"{amount_in_100m:,.0f}억원",
                            "unit": "억원"
                        }
                else:
                    results[metric] = {"error": "값이 없음 (NaN)"}
            else:
                results[metric] = {"error": f"'{metric}' 항목을 찾을 수 없음"}
        
        return results
        
    except KeyError:
        return {"error": f"'{df_key}' 키를 가진 DataFrame을 찾을 수 없습니다."}
    except Exception as e:
        return {"error": f"분석 중 오류 발생: {str(e)}"} 
