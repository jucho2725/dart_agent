# DART 데이터 분석 에이전트 배포 가이드

이 문서는 DART 데이터 분석 에이전트 애플리케이션을 AWS에 배포하는 절차를 설명합니다.

## 사전 준비사항

### 1. AWS CLI 설치 및 설정

AWS CLI가 설치되어 있지 않다면 다음 명령어로 설치합니다:

```bash
# macOS
brew install awscli

# 또는 pip를 사용한 설치
pip install awscli
```

AWS CLI 설정:

```bash
aws configure
```

다음 정보를 입력합니다:
- AWS Access Key ID
- AWS Secret Access Key
- Default region name (예: ap-northeast-2)
- Default output format (json 권장)

### 2. Docker 설치 확인

```bash
docker --version
```

## AWS ECR (Elastic Container Registry) 절차

### 1. ECR 저장소 생성

```bash
# ECR 저장소 생성
aws ecr create-repository \
    --repository-name dart-agent-app \
    --region ap-northeast-2
```

### 2. ECR 로그인

```bash
# AWS ECR에 Docker 로그인 (region을 실제 사용하는 리전으로 변경)
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin [AWS_ACCOUNT_ID].dkr.ecr.ap-northeast-2.amazonaws.com
```

> **참고**: [AWS_ACCOUNT_ID]는 실제 AWS 계정 ID로 교체해야 합니다.

### 3. Docker 이미지 빌드 및 태그

```bash
# 이미지 빌드
docker build -t dart-agent-app .

# ECR용 태그 생성
docker tag dart-agent-app:latest [AWS_ACCOUNT_ID].dkr.ecr.ap-northeast-2.amazonaws.com/dart-agent-app:latest
```

### 4. ECR에 이미지 푸시

```bash
docker push [AWS_ACCOUNT_ID].dkr.ecr.ap-northeast-2.amazonaws.com/dart-agent-app:latest
```

## AWS App Runner 배포 절차

### 1. App Runner 서비스 생성

AWS 콘솔에서 App Runner 서비스를 생성하거나, AWS CLI를 사용합니다:

```bash
aws apprunner create-service \
    --service-name "dart-agent-service" \
    --source-configuration '{
        "ImageRepository": {
            "ImageIdentifier": "[AWS_ACCOUNT_ID].dkr.ecr.ap-northeast-2.amazonaws.com/dart-agent-app:latest",
            "ImageConfiguration": {
                "Port": "8501",
                "RuntimeEnvironmentVariables": {
                    "OPENAI_API_KEY": "your-openai-api-key",
                    "DART_API_KEY": "your-dart-api-key"
                }
            },
            "ImageRepositoryType": "ECR"
        },
        "AutoDeploymentsEnabled": false
    }'
```

### 2. 환경 변수 설정

App Runner 콘솔에서 다음 환경 변수를 설정합니다:

- `OPENAI_API_KEY`: OpenAI API 키
- `DART_API_KEY`: DART API 키
- `PERPLEXITY_API_KEY`: (선택) Perplexity API 키 (research 기능 사용 시)

### 3. 서비스 설정

- **포트**: 8501
- **CPU**: 1 vCPU (최소)
- **메모리**: 2 GB (권장)
- **Auto scaling**: 
  - 최소 인스턴스: 1
  - 최대 인스턴스: 사용량에 따라 조정

## 배포 후 확인

### 1. 서비스 상태 확인

```bash
aws apprunner list-services
```

### 2. 애플리케이션 접속

App Runner가 제공하는 URL로 접속하여 애플리케이션이 정상 작동하는지 확인합니다.

### 3. 로그 확인

```bash
aws apprunner describe-service --service-arn [SERVICE_ARN]
```

## 업데이트 배포

새 버전을 배포하려면:

1. 새 Docker 이미지를 빌드하고 ECR에 푸시
2. App Runner 서비스 업데이트:

```bash
aws apprunner update-service \
    --service-arn [SERVICE_ARN] \
    --source-configuration '{
        "ImageRepository": {
            "ImageIdentifier": "[AWS_ACCOUNT_ID].dkr.ecr.ap-northeast-2.amazonaws.com/dart-agent-app:latest"
        }
    }'
```

## 보안 고려사항

1. **API 키 관리**: 환경 변수로 관리하며, 절대 코드나 이미지에 포함시키지 않습니다.
2. **네트워크 보안**: App Runner의 보안 그룹 설정을 검토합니다.
3. **HTTPS**: App Runner는 기본적으로 HTTPS를 제공합니다.
4. **접근 제어**: 필요시 AWS IAM을 통해 접근을 제한합니다.

## 문제 해결

### 일반적인 문제들

1. **메모리 부족**: 
   - 증상: 애플리케이션이 느리거나 응답하지 않음
   - 해결: App Runner 메모리 설정을 2GB 이상으로 증가

2. **API 키 오류**:
   - 증상: "API key not found" 에러
   - 해결: App Runner 환경 변수 설정 확인

3. **포트 설정 오류**:
   - 증상: 503 Service Unavailable
   - 해결: 포트가 8501로 올바르게 설정되었는지 확인

## 비용 최적화

1. **Auto Scaling 설정**: 사용량이 적은 시간대에는 최소 인스턴스로 운영
2. **ECR 라이프사이클 정책**: 오래된 이미지 자동 삭제 설정
3. **모니터링**: CloudWatch를 통해 사용량 모니터링 및 알림 설정 
