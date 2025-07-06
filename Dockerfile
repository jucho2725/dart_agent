# 베이스 이미지: Python 3.11-slim
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 curl 설치 (healthcheck용)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 의존성 설치 (Docker Layer Caching 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 전체 코드 복사
COPY . .

# Streamlit 기본 포트 8501 개방
EXPOSE 8501

# 컨테이너 상태 확인을 위한 Healthcheck 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8501/_stcore/health

# 컨테이너 실행 명령어 (외부 접속 허용)
CMD ["streamlit", "run", "streamlit/app.py", "--server.port=8501", "--server.address=0.0.0.0"] 
