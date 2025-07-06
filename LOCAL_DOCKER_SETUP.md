# 로컬 Docker 환경 설정 가이드

## Docker Desktop 설치

### macOS

1. [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) 다운로드
2. 다운로드한 `Docker.dmg` 파일 실행
3. Docker 아이콘을 Applications 폴더로 드래그
4. Applications에서 Docker 실행
5. 메뉴바에서 Docker 아이콘이 나타나면 설치 완료

### 설치 확인

```bash
docker --version
docker compose version
```

## 로컬 테스트 절차

### 1. Docker 이미지 빌드

프로젝트 루트 디렉토리에서:

```bash
docker build -t dart-agent-app .
```

### 2. 환경 변수 파일 확인

`.env` 파일이 프로젝트 루트에 있는지 확인하고, 필요한 API 키가 설정되어 있는지 확인:

```bash
# .env 파일 예시
OPENAI_API_KEY=sk-...
DART_API_KEY=your-dart-api-key
PERPLEXITY_API_KEY=your-perplexity-api-key  # 선택사항
```

### 3. Docker 컨테이너 실행

```bash
# .env 파일을 사용하여 컨테이너 실행
docker run -p 8501:8501 --env-file .env dart-agent-app

# 또는 환경 변수를 직접 지정
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=your-openai-api-key \
  -e DART_API_KEY=your-dart-api-key \
  dart-agent-app
```

### 4. 애플리케이션 접속

브라우저에서 `http://localhost:8501` 접속

### 5. 컨테이너 상태 확인

```bash
# 실행 중인 컨테이너 확인
docker ps

# 컨테이너 로그 확인
docker logs <container-id>

# 컨테이너 내부 접속 (디버깅용)
docker exec -it <container-id> /bin/bash
```

## Docker Compose를 사용한 실행 (선택사항)

### docker-compose.yml 파일 생성

```yaml
version: '3.8'

services:
  dart-agent:
    build: .
    ports:
      - "8501:8501"
    env_file:
      - .env
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

### Docker Compose로 실행

```bash
# 빌드 및 실행
docker-compose up --build

# 백그라운드에서 실행
docker-compose up -d

# 종료
docker-compose down
```

## 문제 해결

### 1. 포트 충돌

8501 포트가 이미 사용 중인 경우:

```bash
# 포트 사용 확인
lsof -i :8501

# 다른 포트로 실행
docker run -p 8502:8501 --env-file .env dart-agent-app
```

### 2. 메모리 부족

Docker Desktop 설정에서 메모리 할당량 증가:
- Docker Desktop > Preferences > Resources
- Memory를 최소 4GB 이상으로 설정

### 3. 빌드 캐시 문제

```bash
# 캐시 없이 다시 빌드
docker build --no-cache -t dart-agent-app .
```

## 이미지 관리

```bash
# 이미지 목록 확인
docker images

# 이미지 삭제
docker rmi dart-agent-app

# 사용하지 않는 리소스 정리
docker system prune -a
``` 
