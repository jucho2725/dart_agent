"""
OpenDart API 기능들을 실행하는 메인 파일

사용 방법:
python main.py [기능명] [출력형식]

기능명:
- multi_account: 다중회사 주요계정 정보 조회
- single_account: 단일회사 주요계정 정보 조회
- single_financial: 단일회사 전체 재무제표 조회

출력형식 (선택사항):
- dataframe: DataFrame 형식 출력 (기본값)
- json: JSON 형식 출력
"""

import sys
from tools.opendart import multi_account_main, single_account_main, single_financial_statement_main

def show_usage():
    """사용법을 출력하는 함수"""
    print("OpenDart API 기능 실행")
    print("=" * 40)
    print("사용법: python main.py [기능명] [출력형식]")
    print()
    print("사용 가능한 기능:")
    print("  multi_account     - 다중회사 주요계정 정보 조회")
    print("  single_account    - 단일회사 주요계정 정보 조회")
    print("  single_financial  - 단일회사 전체 재무제표 조회")
    print()
    print("출력형식 (선택사항):")
    print("  dataframe         - DataFrame 형식 출력 (기본값)")
    print("  json              - JSON 형식 출력")
    print()
    print("예시:")
    print("  python main.py multi_account")
    print("  python main.py single_account")
    print("  python main.py single_financial")
    print("  python main.py single_account json")
    print("  python main.py single_financial json")

def main():
    """메인 실행 함수"""
    
    if len(sys.argv) < 2:
        show_usage()
        return
    
    feature = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) >= 3 else "dataframe"
    
    # 출력형식 유효성 검사
    if output_format not in ["dataframe", "json"]:
        print(f"잘못된 출력형식: {output_format}")
        print("가능한 출력형식: dataframe, json")
        return
    
    if feature == "multi_account":
        multi_account_main()
    elif feature == "single_account":
        single_account_main(output_format)
    elif feature == "single_financial":
        single_financial_statement_main(output_format)
    else:
        print(f"알 수 없는 기능: {feature}")
        show_usage()

if __name__ == "__main__":
    main() 
