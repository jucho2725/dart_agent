"""
메인 실행 파일
"""

import sys
import subprocess
import argparse
from agent.graph import run_dart_workflow
from utils.data_store import SessionDataStore
from utils.callbacks import SimpleToolCallbackHandler


def run_console_mode(verbose=False):
    """콘솔 모드로 실행
    
    Args:
        verbose (bool): 상세 출력 모드 여부
    """
    print("DART 데이터 분석 에이전트 (콘솔 모드)")
    print("=" * 50)
    if not verbose:
        print("🔇 간단 출력 모드 (--verbose로 상세 출력 가능)")
    else:
        print("📢 상세 출력 모드")
    
    # 데이터 저장소 초기화
    data_store = SessionDataStore()
    
    # verbose=False일 때 사용할 콜백
    callbacks = [] if verbose else [SimpleToolCallbackHandler()]
    
    while True:
        user_input = input("\n질문을 입력하세요 (종료: exit): ").strip()
        
        if user_input.lower() == 'exit':
            print("프로그램을 종료합니다.")
            break
            
        if not user_input:
            continue
            
        print("\n처리 중...")
        
        try:
            # 워크플로우 실행
            result = run_dart_workflow(
                user_input, 
                data_store, 
                verbose=verbose
            )
            
            # 최종 응답 출력
            for msg in result["messages"]:
                if hasattr(msg, 'content') and not msg.content.startswith("플래너 결정:"):
                    print(f"\n{msg.type.upper()}: {msg.content}")
                    
            # 데이터 저장소 업데이트
            data_store = result["data_store"]
            
            # 저장된 데이터 키 표시
            if data_store.list_keys():
                print(f"\n저장된 데이터 키: {', '.join(data_store.list_keys())}")
                
        except Exception as e:
            print(f"오류 발생: {e}")


def run_streamlit_mode():
    """Streamlit 모드로 실행"""
    print("Streamlit 앱을 시작합니다...")
    # streamlit 명령어를 직접 실행
    subprocess.run(["streamlit", "run", "streamlit/app.py"])


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='DART 데이터 분석 에이전트')
    parser.add_argument('--streamlit', action='store_true', help='Streamlit UI 모드로 실행')
    parser.add_argument('--verbose', action='store_true', help='상세 출력 모드')
    
    args = parser.parse_args()
    
    if args.streamlit:
        run_streamlit_mode()
    else:
        print("\n사용법:")
        print("  콘솔 모드: python main.py")
        print("  콘솔 모드 (상세): python main.py --verbose")
        print("  Streamlit UI: python main.py --streamlit")
        print("  또는 직접 실행: streamlit run streamlit/app.py\n")
        
        run_console_mode(verbose=args.verbose)


if __name__ == "__main__":
    main() 
