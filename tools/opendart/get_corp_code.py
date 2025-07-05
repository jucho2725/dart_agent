import dart_fss as dart
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

def get_api_key():
    """API 키를 가져오는 함수"""
    api_key = os.getenv('DART_API_KEY')
    if not api_key:
        # .env 파일에서 키를 찾을 수 없는 경우 직접 입력 요청
        print("API 키를 찾을 수 없습니다. 직접 입력해주세요.")
        api_key = input("OpenDart API 키를 입력하세요: ")
    return api_key

def find_corp_code_by_name(api_key, company_name, exactly=True):
    """회사 이름으로 corp_code를 찾는 함수"""
    try:
        # dart_fss 라이브러리에 API 키 설정
        dart.set_api_key(api_key=api_key)
        
        # 회사 검색
        corp_list = dart.get_corp_list()
        companies = corp_list.find_by_corp_name(company_name, exactly=exactly)
        
        if companies:
            if len(companies) == 1:
                corp_code = companies[0].corp_code
                corp_name = companies[0].corp_name
                print(f"{corp_name}의 corp_code: {corp_code}")
                return corp_code
            else:
                print(f"'{company_name}'로 검색된 회사가 {len(companies)}개 있습니다:")
                for i, corp in enumerate(companies):
                    print(f"  {i+1}. {corp.corp_name} ({corp.corp_code})")
                
                # 사용자에게 선택 요청
                while True:
                    try:
                        choice = input(f"선택하세요 (1-{len(companies)}): ")
                        choice_idx = int(choice) - 1
                        if 0 <= choice_idx < len(companies):
                            selected_corp = companies[choice_idx]
                            corp_code = selected_corp.corp_code
                            corp_name = selected_corp.corp_name
                            print(f"{corp_name}의 corp_code: {corp_code}")
                            return corp_code
                        else:
                            print("올바른 번호를 입력하세요.")
                    except ValueError:
                        print("숫자를 입력하세요.")
        else:
            print(f"'{company_name}'를 찾을 수 없습니다.")
            
            # 정확히 일치하지 않는 경우 부분 검색 시도
            if exactly:
                print("부분 일치 검색을 시도합니다...")
                return find_corp_code_by_name(api_key, company_name, exactly=False)
            
            return None
            
    except Exception as e:
        print(f"corp_code 검색 중 오류 발생: {e}")
        return None

def find_samsung_corp_code(api_key):
    """삼성전자의 corp_code를 찾는 함수 (테스트용)"""
    return find_corp_code_by_name(api_key, '삼성전자', exactly=True)

def get_corp_code_interactive():
    """대화형으로 회사 코드를 찾는 함수"""
    print("OpenDart 회사 코드 찾기")
    print("=" * 30)
    
    # API 키 가져오기
    api_key = get_api_key()
    if not api_key:
        print("API 키가 없어 종료합니다.")
        return None
    
    # 회사 이름 입력
    company_name = input("회사 이름을 입력하세요: ").strip()
    if not company_name:
        print("회사 이름이 입력되지 않았습니다.")
        return None
    
    # corp_code 찾기
    corp_code = find_corp_code_by_name(api_key, company_name)
    return corp_code

if __name__ == "__main__":
    # 직접 실행시 대화형 모드
    get_corp_code_interactive() 
