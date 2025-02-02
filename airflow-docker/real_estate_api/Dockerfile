# 권장되는 기본 구조
FROM python:3.9-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 시작 스크립트 생성
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]