"""
LangChain 도구로 변환된 OpenDart API 함수들 - DataFrame 반환 버전
"""

from langchain.tools import tool
from typing import Optional, Dict, Any, Tuple
import dart_fss as dart
from dotenv import load_dotenv
import os
import pandas as pd

from .get_corp_code import find_corp_code_by_name
from .get_financial_statement import get_financial_statement_for_company
from utils.data_store import SessionDataStore

# .env 파일 로드
load_dotenv()

# 전역 데이터 저장소 (OpendartAgent 생성 시 설정됨)
_global_data_store: Optional[SessionDataStore] = None


def set_data_store(data_store: SessionDataStore):
    """OpendartAgent가 사용할 데이터 저장소를 설정합니다."""
    global _global_data_store
    _global_data_store = data_store


def get_api_key():
    """API 키를 가져오는 함수"""
    api_key = os.getenv('DART_API_KEY')
    if not api_key:
        raise ValueError("DART_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
    return api_key


@tool
def search_corp_code(company_name: str) -> Optional[Dict[str, str]]:
    """
    회사명으로 DART 시스템의 고유번호(corp_code)를 검색합니다.
    
    이 도구는 한국 기업의 이름을 입력받아 전자공시시스템(DART)에서 사용하는 
    8자리 고유번호를 찾아 반환합니다. 재무제표나 공시 정보를 조회하기 전에 
    반드시 이 도구를 사용하여 corp_code를 먼저 획득해야 합니다.
    
    Args:
        company_name (str): 검색할 회사명 (예: '삼성전자', '카카오', 'SK하이닉스')
                           - 정확한 회사명을 입력하면 더 정확한 결과를 얻을 수 있습니다
                           - 부분 명칭도 가능하나, 여러 결과가 나올 수 있습니다
    
    Returns:
        Dict[str, str]: 성공 시 {'corp_code': '00126380', 'corp_name': '삼성전자'} 형태의 딕셔너리
                       실패 시 None
    
    Examples:
        - "삼성전자의 고유번호 찾아줘" → search_corp_code("삼성전자")
        - "카카오 corp_code 검색" → search_corp_code("카카오")
        - "Find SK Hynix code" → search_corp_code("SK하이닉스")
    """
    try:
        api_key = get_api_key()
        
        # dart_fss 라이브러리에 API 키 설정
        dart.set_api_key(api_key=api_key)
        
        # 회사 검색
        corp_list = dart.get_corp_list()
        companies = corp_list.find_by_corp_name(company_name, exactly=True)
        
        if not companies:
            # 정확한 매칭이 없으면 부분 검색 시도
            companies = corp_list.find_by_corp_name(company_name, exactly=False)
        
        if companies:
            # 첫 번째 결과 반환 (가장 유사한 매칭)
            selected_corp = companies[0]
            return {
                'corp_code': selected_corp.corp_code,
                'corp_name': selected_corp.corp_name
            }
        else:
            return None
            
    except Exception as e:
        # print 대신 오류 정보를 반환
        return None


def search_financial_statements_dataframe(
    company_name: str,
    year: Optional[str] = "2023",
    report_type: Optional[str] = "annual",
    fs_type: Optional[str] = "consolidated",
    save_to_store: bool = True,
    data_store: Optional[SessionDataStore] = None
) -> Tuple[Optional[pd.DataFrame], str]:
    """
    회사의 재무제표 정보를 DataFrame 형태로 조회하고 저장합니다.
    
    Args:
        company_name (str): 조회할 회사명
        year (str): 조회할 사업연도
        report_type (str): 보고서 유형 (annual/half/quarter)
        fs_type (str): 재무제표 유형 (consolidated/separate)
        save_to_store (bool): SessionDataStore에 저장 여부
        data_store (SessionDataStore): 데이터 저장소 (None이면 전역 저장소 사용)
    
    Returns:
        Tuple[Optional[pd.DataFrame], str]: (DataFrame, 메시지) 튜플
    """
    try:
        api_key = get_api_key()
        
        # 기본값 설정
        report_type = report_type or "annual"
        fs_type = fs_type or "consolidated"
        year = year or "2023"
        
        # 보고서 코드 매핑
        report_code_map = {
            "annual": "11011",
            "half": "11012",
            "quarter": "11014",
            "q1": "11013",
        }
        
        # 재무제표 구분 매핑
        fs_div_map = {
            "consolidated": "CFS",
            "separate": "OFS",
        }
        
        # 입력값 변환
        reprt_code = report_code_map.get(report_type.lower(), "11011")
        fs_div = fs_div_map.get(fs_type.lower(), "CFS")
        
        # 1. corp_code 찾기
        corp_info = search_corp_code(company_name)
        if not corp_info:
            return None, f"'{company_name}'의 기업 코드를 찾을 수 없습니다."
        
        # corp_info가 Dict인지 확인
        if isinstance(corp_info, dict):
            corp_code = corp_info.get('corp_code', '')
            actual_company_name = corp_info.get('corp_name', company_name)
        else:
            # 예상치 못한 타입인 경우
            corp_code = str(corp_info)
            actual_company_name = company_name
        
        # 2. 재무제표 데이터 조회
        results = get_financial_statement_for_company(
            api_key=api_key,
            corp_code=corp_code,
            company_name=actual_company_name,
            output_format="dataframe",
            bsns_year=year,
            reprt_code=reprt_code,
            verbose=False  # verbose=False로 설정하여 상세 출력 억제
        )
        
        if not results:
            return None, f"'{actual_company_name}'의 {year}년 재무제표를 찾을 수 없습니다."
        
        # 3. 적절한 DataFrame 선택
        selected_df = None
        for fs_name, (df, raw_data) in results.items():
            if "연결" in fs_name and fs_type == "consolidated":
                selected_df = df
                break
            elif "개별" in fs_name and fs_type == "separate":
                selected_df = df
                break
        
        if selected_df is None:
            return None, f"요청한 재무제표 유형 '{fs_type}'을 찾을 수 없습니다."
        
        # 4. SessionDataStore에 저장
        if save_to_store:
            # 전역 데이터 저장소 사용
            if data_store is None:
                data_store = _global_data_store
            
            if data_store is None:
                # 전역 저장소도 없으면 새로 생성
                data_store = SessionDataStore()
            
            # 키 생성 (예: samsung_fs_2023_consolidated)
            key_parts = [
                actual_company_name.replace(' ', '_').lower(),
                'fs',
                year,
                fs_type
            ]
            storage_key = '_'.join(key_parts)
            
            # 이미 존재하는 키인지 확인
            existing_keys = data_store.list_keys()
            if storage_key not in existing_keys:
                # DataFrame 저장
                data_store.add(storage_key, selected_df)
                
                # 전역 데이터 저장소에도 추가 (중복 확인)
                if _global_data_store and data_store != _global_data_store:
                    global_keys = _global_data_store.list_keys()
                    if storage_key not in global_keys:
                        _global_data_store.add(storage_key, selected_df)
                
                message = f"'{actual_company_name}'의 {year}년 {fs_type} 재무제표를 조회하여 '{storage_key}' 키로 저장했습니다."
            else:
                message = f"'{actual_company_name}'의 {year}년 {fs_type} 재무제표가 이미 '{storage_key}' 키로 저장되어 있습니다."
        else:
            message = f"'{actual_company_name}'의 {year}년 {fs_type} 재무제표를 조회했습니다."
        
        return selected_df, message
        
    except Exception as e:
        return None, f"재무제표 조회 중 오류 발생: {e}"


@tool
def search_financial_statements(
    company_name: str,
    year: Optional[str] = "2023",
    report_type: Optional[str] = "annual",
    fs_type: Optional[str] = "consolidated",
    return_format: str = "summary"
) -> Optional[Dict[str, Any]]:
    """
    회사의 재무제표 정보를 조회합니다.
    
    이 도구는 한국 기업의 재무제표(재무상태표, 손익계산서, 현금흐름표 등)를 
    OpenDART API를 통해 조회합니다. 회사명을 입력하면 자동으로 corp_code를 
    검색한 후 재무제표 데이터를 가져옵니다.
    
    Args:
        company_name (str): 조회할 회사명 (예: '삼성전자', 'LG전자', 'NAVER')
        
        year (str, optional): 조회할 사업연도. 기본값은 "2023"
                            - "2024", "2023", "2022" 등 4자리 연도
                            
        report_type (str, optional): 보고서 유형. 기본값은 "annual"
                                   - "annual": 사업보고서 (연간)
                                   - "half": 반기보고서
                                   - "quarter": 분기보고서
                                   
        fs_type (str, optional): 재무제표 유형. 기본값은 "consolidated"
                               - "consolidated": 연결재무제표 (자회사 포함)
                               - "separate": 별도재무제표 (개별 기업만)
                               
        return_format (str, optional): 반환 형식. 기본값은 "summary"
                                     - "summary": 주요 항목 요약
                                     - "dataframe": 전체 DataFrame 정보
    
    Returns:
        Dict[str, Any]: 재무제표 정보를 포함한 딕셔너리
    
    Examples:
        - "삼성전자 2024년 재무제표 보여줘" 
          → search_financial_statements("삼성전자", year="2024")
        
        - "카카오 작년 연결재무제표 찾아줘"
          → search_financial_statements("카카오", year="2023", fs_type="consolidated")
    """
    # DataFrame 조회 및 저장
    df, message = search_financial_statements_dataframe(
        company_name=company_name,
        year=year,
        report_type=report_type,
        fs_type=fs_type,
        save_to_store=True
    )
    
    if df is None:
        return {
            'status': 'error',
            'message': message
        }
    
    # 반환 형식에 따른 처리
    if return_format == "dataframe":
        # DataFrame 정보 반환
        return {
            'status': 'success',
            'message': message,
            'data_info': {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist(),
                'sample_data': df.head(5).to_dict()
            }
        }
    else:
        # 기본: 주요 항목 요약 반환
        key_items = extract_key_financial_items(df)
        
        # 금액을 억원 단위로 변환
        formatted_items = {}
        for item, amount in key_items.items():
            if amount is not None:
                amount_in_100m = amount / 100_000_000  # 억원 단위
                if amount_in_100m >= 10000:
                    amount_in_t = amount_in_100m / 10000  # 조원 단위
                    formatted_items[item] = f"{amount_in_t:,.1f}조원"
                else:
                    formatted_items[item] = f"{amount_in_100m:,.0f}억원"
        
        return {
            'status': 'success',
            'message': message,
            'company_name': company_name,
            'year': year,
            'fs_type': fs_type,
            'financial_summary': formatted_items
        }


def extract_key_financial_items(df):
    """DataFrame에서 주요 재무 항목을 추출하는 헬퍼 함수"""
    key_items = {}
    
    if df is None or df.empty:
        return key_items
    
    # 재무상태표 항목
    bs_items = ['자산총계', '부채총계', '자본총계', '유동자산', '비유동자산']
    
    # 손익계산서 항목  
    is_items = ['매출액', '매출총이익', '영업이익', '당기순이익']
    
    # 재무상태표 데이터 추출
    bs_data = df[df['sj_div'] == 'BS']
    for item in bs_items:
        item_data = bs_data[bs_data['account_nm'].str.contains(item, na=False)]
        if not item_data.empty and 'thstrm_amount' in item_data.columns:
            amount = item_data['thstrm_amount'].iloc[0]
            if pd.notna(amount):
                key_items[item] = int(amount)
    
    # 손익계산서 데이터 추출
    is_data = df[df['sj_div'] == 'IS']
    for item in is_items:
        item_data = is_data[is_data['account_nm'].str.contains(item, na=False)]
        if not item_data.empty and 'thstrm_amount' in item_data.columns:
            amount = item_data['thstrm_amount'].iloc[0]
            if pd.notna(amount):
                key_items[item] = int(amount)
    
    return key_items 
