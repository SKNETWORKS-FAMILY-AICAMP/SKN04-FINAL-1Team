    # 권장되는 기본 구조
FROM python:3.9-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# start.sh 스크립트 설정
RUN sed -i 's/\r$//' start.sh && \
    chmod +x start.sh

# 실행
CMD ["sh", "start.sh"]