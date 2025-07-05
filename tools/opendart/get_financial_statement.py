import requests
import json
import pandas as pd
from pprint import pprint
from .get_corp_code import get_api_key, find_corp_code_by_name, find_samsung_corp_code

def get_single_financial_statement(api_key, corp_code, bsns_year="2023", reprt_code="11011", fs_div="CFS"):
    """OpenDart API를 통해 단일회사 전체 재무제표 정보를 받아오는 함수"""
    
    # API 요청 URL
    url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
    
    # 요청 인자 설정
    params = {
        "crtfc_key": api_key,        # API 인증키
        "corp_code": corp_code,      # 고유번호
        "bsns_year": bsns_year,      # 사업연도
        "reprt_code": reprt_code,    # 보고서 코드 (11011: 사업보고서)
        "fs_div": fs_div             # 개별/연결구분 (CFS: 연결재무제표, OFS: 재무제표)
    }
    
    try:
        # API 요청
        response = requests.get(url, params=params)
        response.raise_for_status()  # HTTP 에러 체크
        
        # JSON 응답 파싱
        data = response.json()
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류 발생: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        return None

def convert_to_dataframe(data):
    """API 응답 데이터를 DataFrame으로 변환하는 함수"""
    
    if not data or 'list' not in data:
        print("변환할 데이터가 없습니다.")
        return None
    
    try:
        # 리스트 데이터를 DataFrame으로 변환
        df = pd.DataFrame(data['list'])
        
        # 금액 컬럼들을 숫자 타입으로 변환
        amount_columns = ['thstrm_amount', 'thstrm_add_amount', 'frmtrm_amount', 
                         'frmtrm_q_amount', 'frmtrm_add_amount', 'bfefrmtrm_amount']
        
        for col in amount_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
        
        # ord 컬럼을 숫자 타입으로 변환
        if 'ord' in df.columns:
            df['ord'] = pd.to_numeric(df['ord'], errors='coerce')
        
        return df
        
    except Exception as e:
        print(f"DataFrame 변환 중 오류 발생: {e}")
        return None

def analyze_financial_statements(df):
    """재무제표 데이터를 분석하는 함수"""
    
    if df is None or df.empty:
        print("분석할 데이터가 없습니다.")
        return
    
    print("=" * 80)
    print("재무제표 분석 결과")
    print("=" * 80)
    
    # 기본 정보
    print(f"총 데이터 건수: {len(df)}")
    print(f"재무제표 구분: {df['sj_div'].unique()}")
    print(f"재무제표명: {df['sj_nm'].unique()}")
    print()
    
    # 재무제표별 데이터 수
    print("재무제표별 계정 수:")
    statement_counts = df.groupby(['sj_div', 'sj_nm']).size()
    for (div, name), count in statement_counts.items():
        print(f"  {div} ({name}): {count}개 계정")
    print()
    
    # 주요 계정 분석 (당기금액 기준)
    if 'thstrm_amount' in df.columns:
        # 금액이 있는 데이터만 필터링
        amount_data = df[df['thstrm_amount'].notna() & (df['thstrm_amount'] != 0)]
        
        if not amount_data.empty:
            print("주요 계정별 당기금액 (상위 15개):")
            print("-" * 60)
            
            # 절댓값 기준으로 정렬
            top_accounts = amount_data.nlargest(15, 'thstrm_amount')
            
            for _, row in top_accounts.iterrows():
                account_name = row['account_nm']
                amount = row['thstrm_amount']
                sj_nm = row['sj_nm']
                
                # 금액을 조 단위로 표시
                amount_in_trillion = amount / 1_000_000_000_000
                print(f"  {account_name[:30]:<30} {amount_in_trillion:>8.1f}조원 ({sj_nm})")
            print()
    
    # 재무상태표 주요 항목 (BS)
    bs_data = df[df['sj_div'] == 'BS']
    if not bs_data.empty:
        print("재무상태표 주요 항목:")
        print("-" * 40)
        key_accounts = ['자산총계', '부채총계', '자본총계', '유동자산', '비유동자산', '유동부채', '비유동부채']
        
        for account in key_accounts:
            account_data = bs_data[bs_data['account_nm'].str.contains(account, na=False)]
            if not account_data.empty and 'thstrm_amount' in account_data.columns:
                latest_amount = account_data['thstrm_amount'].iloc[0]
                if pd.notna(latest_amount):
                    amount_in_trillion = latest_amount / 1_000_000_000_000
                    print(f"  {account:<10}: {amount_in_trillion:>8.1f}조원")
        print()
    
    # 손익계산서 주요 항목 (IS)
    is_data = df[df['sj_div'] == 'IS']
    if not is_data.empty:
        print("손익계산서 주요 항목:")
        print("-" * 40)
        key_accounts = ['매출액', '매출총이익', '영업이익', '당기순이익', '매출원가']
        
        for account in key_accounts:
            account_data = is_data[is_data['account_nm'].str.contains(account, na=False)]
            if not account_data.empty and 'thstrm_amount' in account_data.columns:
                latest_amount = account_data['thstrm_amount'].iloc[0]
                if pd.notna(latest_amount):
                    amount_in_trillion = latest_amount / 1_000_000_000_000
                    print(f"  {account:<10}: {amount_in_trillion:>8.1f}조원")
        print()

def print_dataframe_info(df, data):
    """DataFrame 정보를 출력하는 함수"""
    
    if df is None or df.empty:
        print("출력할 데이터가 없습니다.")
        return
    
    print("=" * 80)
    print("OpenDart API 응답 결과 - 단일회사 전체 재무제표")
    print("=" * 80)
    
    # 상태 정보 출력
    if 'status' in data:
        print(f"상태 코드: {data['status']}")
        print(f"메시지: {data.get('message', 'N/A')}")
        print()
    
    # DataFrame 기본 정보
    print("DataFrame 정보:")
    print(f"  - 행 수: {len(df)}")
    print(f"  - 열 수: {len(df.columns)}")
    print(f"  - 컬럼: {list(df.columns)}")
    print()
    
    # 재무제표 분석
    analyze_financial_statements(df)
    
    print("=" * 80)
    print("샘플 데이터 (처음 10개):")
    print("=" * 80)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(df.head(10))
    
    print("\n" + "=" * 80)
    print("전체 DataFrame 정보:")
    print("=" * 80)
    print(df.info())

def convert_to_json(df, indent=2):
    """DataFrame을 JSON 형식으로 변환하는 함수"""
    
    if df is None or df.empty:
        print("변환할 DataFrame이 없습니다.")
        return None
    
    try:
        # DataFrame을 JSON으로 변환 (records 형식으로)
        json_data = df.to_json(orient='records', force_ascii=False, indent=indent)
        return json_data
        
    except Exception as e:
        print(f"JSON 변환 중 오류 발생: {e}")
        return None

def save_as_json(df, filename):
    """DataFrame을 JSON 파일로 저장하는 함수"""
    
    try:
        json_data = convert_to_json(df)
        if json_data:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json_data)
            print(f"JSON 파일이 '{filename}'로 저장되었습니다.")
            return True
        else:
            print("저장할 JSON 데이터가 없습니다.")
            return False
            
    except Exception as e:
        print(f"JSON 파일 저장 중 오류 발생: {e}")
        return False

def print_json_output(df, title):
    """DataFrame을 JSON 형식으로 출력하는 함수"""
    
    if df is None or df.empty:
        print(f"{title} - 출력할 데이터가 없습니다.")
        return
    
    print("=" * 80)
    print(f"{title} - JSON 형식 출력")
    print("=" * 80)
    
    json_data = convert_to_json(df, indent=2)
    if json_data:
        # JSON이 너무 길 경우 처음 부분만 출력
        if len(json_data) > 5000:
            print(f"{json_data[:5000]}...")
            print(f"\n[JSON 데이터가 길어서 처음 5000자만 표시했습니다. 전체 데이터는 파일에서 확인하세요.]")
        else:
            print(json_data)
    else:
        print("JSON 변환에 실패했습니다.")

def get_financial_statement_for_company(api_key, corp_code, company_name, output_format="dataframe", bsns_year="2023", reprt_code="11011"):
    """특정 회사의 단일회사 전체 재무제표 데이터를 조회하는 함수"""
    
    print(f"OpenDart API를 활용한 {company_name} 전체 재무제표 조회")
    print("=" * 60)
    
    # 1. 재무제표 정보 가져오기
    print("\n1. 재무제표 정보 조회 중...")
    
    # 연결재무제표와 개별재무제표 모두 조회
    results = {}
    fs_types = [
        ("CFS", "연결재무제표"),
        ("OFS", "개별재무제표")
    ]
    
    for fs_div, fs_name in fs_types:
        print(f"  - {fs_name} 조회 중...")
        print(f"    요청 인자:")
        print(f"      corp_code: {corp_code}")
        print(f"      bsns_year: {bsns_year}")
        print(f"      reprt_code: {reprt_code} (사업보고서)")
        print(f"      fs_div: {fs_div} ({fs_name})")
        
        financial_data = get_single_financial_statement(api_key, corp_code, bsns_year, reprt_code, fs_div)
        
        if financial_data:
            # DataFrame으로 변환
            df = convert_to_dataframe(financial_data)
            if df is not None:
                results[fs_name] = (df, financial_data)
                print(f"    성공: {len(df)}건의 데이터 조회")
            else:
                print(f"    실패: DataFrame 변환 오류")
        else:
            print(f"    실패: API 호출 오류")
        print()
    
    if not results:
        print("조회된 재무제표 데이터가 없습니다.")
        return None
    
    # 2. 결과 출력 및 저장 (형식에 따라)
    if output_format == "json":
        print("2. 결과 출력 (JSON 형식):")
        
        for fs_name, (df, raw_data) in results.items():
            print(f"\n{'='*20} {fs_name} {'='*20}")
            print_json_output(df, fs_name)
            
            # JSON 파일로 저장
            json_filename = f"{company_name}_{fs_name.replace('재무제표', '')}_financial_statement.json"
            try:
                save_as_json(df, json_filename)
            except Exception as e:
                print(f"JSON 파일 저장 중 오류 발생: {e}")
    else:
        print("2. 결과 출력 (DataFrame 형식):")
        
        for fs_name, (df, raw_data) in results.items():
            print(f"\n{'='*20} {fs_name} {'='*20}")
            print_dataframe_info(df, raw_data)
            
            # CSV 파일로 저장
            csv_filename = f"{company_name}_{fs_name.replace('재무제표', '')}_financial_statement.csv"
            try:
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"\n{fs_name} 결과가 '{csv_filename}' 파일로 저장되었습니다.")
            except Exception as e:
                print(f"파일 저장 중 오류 발생: {e}")
    
    return results

def main(company_name=None, output_format="dataframe", bsns_year="2023", reprt_code="11011"):
    """메인 실행 함수"""
    
    # 1. API 키 가져오기
    api_key = get_api_key()
    if not api_key:
        print("API 키가 없어 종료합니다.")
        return None
    
    # 2. 회사명이 주어지지 않은 경우 입력 요청
    if not company_name:
        company_name = input("회사 이름을 입력하세요: ").strip()
        if not company_name:
            print("회사 이름이 입력되지 않았습니다.")
            return None
    
    # 3. corp_code 찾기
    print(f"\n1. {company_name} corp_code 검색 중...")
    corp_code = find_corp_code_by_name(api_key, company_name)
    if not corp_code:
        print(f"{company_name}의 corp_code를 찾을 수 없어 종료합니다.")
        return None
    
    # 4. 재무제표 데이터 조회
    return get_financial_statement_for_company(api_key, corp_code, company_name, output_format, bsns_year, reprt_code)

def test_samsung():
    """삼성전자 테스트 함수"""
    print("삼성전자 테스트 케이스 실행")
    print("=" * 40)
    
    # API 키 가져오기
    api_key = get_api_key()
    if not api_key:
        print("API 키가 없어 종료합니다.")
        return None
    
    # 삼성전자 corp_code 찾기
    print("\n1. 삼성전자 corp_code 검색 중...")
    corp_code = find_samsung_corp_code(api_key)
    if not corp_code:
        print("삼성전자의 corp_code를 찾을 수 없어 종료합니다.")
        return None
    
    # 삼성전자 재무제표 데이터 조회
    return get_financial_statement_for_company(api_key, corp_code, "삼성전자", "dataframe")

if __name__ == "__main__":
    # 직접 실행시 삼성전자 테스트 케이스 실행
    test_samsung() 
