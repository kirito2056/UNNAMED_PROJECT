# 1. Use an official Python runtime as a parent image
# 1. 공식 파이썬 런타임을 부모 이미지로 사용
FROM python:3.11-slim

# Install system dependencies needed for building Python packages
# Python 패키지 빌드에 필요한 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 2. Set the working directory in the container
# 2. 컨테이너 내 작업 디렉토리 설정
WORKDIR /app

# 3. Set environment variables
# 3. 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 4. Install dependencies
# 4. 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application code
# 5. 나머지 애플리케이션 코드 복사
COPY ./app /app/app

# The command to run the application will be provided by docker-compose
# 애플리케이션 실행 명령어는 docker-compose에서 제공될 예정
# Default command (can be overridden): uvicorn app.main:app --host 0.0.0.0 --port 8000
# 기본 명령어 (오버라이드 가능): uvicorn app.main:app --host 0.0.0.0 --port 8000
