import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DART_API_KEY = os.getenv("DART_API_KEY")

# API 키 유효성 검사 (개발 시에는 경고만 표시)
def validate_api_keys():
    """API 키의 유효성을 검사하고 경고를 표시합니다."""
    missing_keys = []
    
    if not OPENAI_API_KEY:
        missing_keys.append("OPENAI_API_KEY")
    if not DART_API_KEY:
        missing_keys.append("DART_API_KEY")
    
    if missing_keys:
        print(f"경고: 다음 API 키들이 .env 파일에 설정되지 않았습니다: {', '.join(missing_keys)}")
        print("실제 사용 시에는 .env 파일에 올바른 API 키를 설정해주세요.")
        return False
    
    return True

# 초기 검사 실행
is_configured = validate_api_keys() 

def get_openai_api_key():
    """OpenAI API 키를 반환합니다."""
    return OPENAI_API_KEY

def get_dart_api_key():
    """DART API 키를 반환합니다."""
    return DART_API_KEY

def load_env():
    """환경 변수를 다시 로드합니다."""
    load_dotenv(override=True) 
