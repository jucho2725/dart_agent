"""
DART 에이전트 시스템에서 사용되는 프롬프트 템플릿들을 관리하는 모듈입니다.
"""

# 기본 시스템 프롬프트
DEFAULT_SYSTEM_PROMPT = """
당신은 DART(전자공시시스템) 데이터 분석 전문가입니다.
사용자의 요청에 따라 기업의 재무 데이터를 수집하고 분석하여 
명확하고 유용한 정보를 제공합니다.
"""

# 데이터 수집 프롬프트
DATA_COLLECTION_PROMPT = """
다음 기업의 재무 데이터를 수집해주세요:
기업명: {company_name}
보고서 유형: {report_type}
기간: {period}
"""

# 분석 프롬프트
ANALYSIS_PROMPT = """
수집된 데이터를 바탕으로 다음 분석을 수행해주세요:
분석 유형: {analysis_type}
주요 지표: {key_metrics}
""" 
