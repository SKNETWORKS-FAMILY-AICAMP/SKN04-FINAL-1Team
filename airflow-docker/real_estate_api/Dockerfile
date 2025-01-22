# 권장되는 기본 구조
FROM python:3.9-slim

# 시스템 의존성 한번에 설치
RUN apt-get update && \
    apt-get install -y \
    netcat-traditional \
    postgresql-client \
    # 기타 필요한 시스템 패키지들... \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# entrypoint 스크립트 설정
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]