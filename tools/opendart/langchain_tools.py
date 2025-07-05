"""
LangChain 도구로 변환된 OpenDart API 함수들
"""

from langchain.tools import tool
from typing import Optional, Dict, Any
import dart_fss as dart
from dotenv import load_dotenv
import os

from .get_corp_code import find_corp_code_by_name
from .get_financial_statement import get_financial_statement_for_company

# .env 파일 로드
load_dotenv()

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
        print(f"corp_code 검색 중 오류 발생: {e}")
        return None


@tool
def search_financial_statements(
    company_name: str,
    year: Optional[str] = "2023",
    report_type: Optional[str] = "annual",
    fs_type: Optional[str] = "consolidated"
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
    
    Returns:
        Dict[str, Any]: 재무제표 데이터를 포함한 딕셔너리
                       - 'company_name': 회사명
                       - 'corp_code': 기업 고유번호
                       - 'year': 사업연도
                       - 'financial_data': 재무제표 상세 데이터
                       실패 시 None
    
    Examples:
        - "삼성전자 2024년 재무제표 보여줘" 
          → search_financial_statements("삼성전자", year="2024")
        
        - "카카오 작년 연결재무제표 찾아줘"
          → search_financial_statements("카카오", year="2023", fs_type="consolidated")
          
        - "네이버 반기보고서 재무제표 조회"
          → search_financial_statements("네이버", report_type="half")
    """
    try:
        api_key = get_api_key()
        
        # 보고서 코드 매핑
        report_code_map = {
            "annual": "11011",      # 사업보고서
            "half": "11012",        # 반기보고서
            "quarter": "11014",     # 3분기보고서
            "q1": "11013",          # 1분기보고서
        }
        
        # 재무제표 구분 매핑
        fs_div_map = {
            "consolidated": "CFS",  # 연결재무제표
            "separate": "OFS",      # 개별재무제표
        }
        
        # 입력값 변환
        reprt_code = report_code_map.get(report_type.lower(), "11011")
        
        # 1. corp_code 찾기
        corp_info = search_corp_code(company_name)
        if not corp_info:
            return None
        
        corp_code = corp_info['corp_code']
        actual_company_name = corp_info['corp_name']
        
        # 2. 재무제표 데이터 조회
        results = get_financial_statement_for_company(
            api_key=api_key,
            corp_code=corp_code,
            company_name=actual_company_name,
            output_format="dataframe",
            bsns_year=year,
            reprt_code=reprt_code
        )
        
        if not results:
            return None
        
        # 3. 결과 정리
        financial_data = {}
        for fs_name, (df, raw_data) in results.items():
            # 주요 계정 항목만 추출
            if "연결" in fs_name and fs_type == "consolidated":
                financial_data = extract_key_financial_items(df)
                break
            elif "개별" in fs_name and fs_type == "separate":
                financial_data = extract_key_financial_items(df)
                break
        
        return {
            'company_name': actual_company_name,
            'corp_code': corp_code,
            'year': year,
            'report_type': report_type,
            'fs_type': fs_type,
            'financial_data': financial_data
        }
        
    except Exception as e:
        print(f"재무제표 조회 중 오류 발생: {e}")
        return None


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


# pandas import 추가
import pandas as pd 
