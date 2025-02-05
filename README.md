# 서집사

---
서집사는 부동산을 처음 접하는 20~30대 청년들을 위해서 제작된 **AI 기반 부동산 매물 검색 및 추천 챗봇** 서비스입니다. 청년들의 부동산 접근성을 높여주고 개인화된 서비스를 제공합니다.

LangGraph를 사용하여 고객 친화적인 대화 시스템과 부동산 매물 조회 시스템을 구축하였습니다. AWS의 EC2를 이용하여 제공되며 Docker를 이용하여 전체 시스템의 환경을 일정하게 관리합니다.

---

 
### 🤭 팀원

<p align="center">
  <table>
	<tr>
	  <td align="center">
		<img src="https://pbs.twimg.com/media/D07FPC9WwAYZ1k1.jpg" width="160" height="160"/><br>김정훈<br>[팀장]
	  </td>
	  <td align="center">
		<img src="https://upload3.inven.co.kr/upload/2020/04/15/bbs/i13843617916.jpg" width="160" height="160"/><br>김태욱
	  </td>
	  <td align="center">
		<img src="https://i.namu.wiki/i/CFdrduUAhyuiXzPMZ-WKsUJtGCuWOvzYLcIAdrcjZ2D7x4q3W1TxkGIYmBKTohKEM1vUNtgeZtilVHwCe2q17g.webp" width="160" height="160"/><br>박화랑
	  </td>
	  <td align="center">
		<img src="https://opgg-static.akamaized.net/meta/images/profile_icons/profileIcon4895.jpg?image=e_upscale,q_auto:good,f_webp,w_auto&v=1729058249" width="160" height="160"/><br>박진효
	  </td>
	</tr>
  </table>
</p>




### 💼 역할 분담

### 👨‍💻 김정훈
- **Backend**: Streamlit으로 구현된 페이지를 Django로 이식 (공동작업)
- **데이터수집**: Airflow를 이용해서 데이터를 수집하고 API를 
- **README.md 작성**

### 👨‍💻 김태욱
- **Frontend**: Streamlit으로 구현된 페이지를 html 형식으로 변경 (공동작업) 
- **요구사항 정의서 작성** : 

### 👩‍💻 박화랑
- **AI**: LangChain 구성 및 연결, 질문-SQL Query 제작 (공동작업)
- **RAG**: Chroma를 이용한 VectorDB 구축, RAG 구성 및 LLM 연동

### 👨‍💻 박진효
- **AI**: Prompt 작성 및 모델 성능 개선
- **AWS 배포**: Django로 제작된 페이지를 AWS환경에서 배포

---




## 기술 스텍

| Data Collection | AI | SCM | Front-End / Back-End | Deploy |
|-------------|-----------------|----------|---------------------|------------------|
|  ![Airflow](https://img.shields.io/badge/Airflow-017CEE?style=for-the-badge&logo=Apache%20Airflow&logoColor=white) ![Tor](https://img.shields.io/badge/Tor_Browser-7D4698?style=for-the-badge&logo=Tor-Browser&logoColor=white) |![openAI](https://img.shields.io/badge/openai-412991?style=for-the-badge&logo=openai&logoColor=white") ![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?logo=langgraph&logoColor=fff&style=flat-square)|![Git](https://img.shields.io/badge/GIT-E44C30?style=for-the-badge&logo=git&logoColor=white")| ![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB) ![django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white) | ![AWS](https://img.shields.io/badge/Amazon_AWS-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)  ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=Docker&logoColor=white)|

## Prerequisites


### .env 환경변수 파일 필요 

```
AIRFLOW_UID=****************
AIRFLOW_GID=****************

# API Keys
KAKAO_API_KEY=****************
SEOUL_API_KEY=****************

# Database
POSTGRES_USER=****************
POSTGRES_PASSWORD=****************
POSTGRES_DB=****************
POSTGRES_HOST=****************
POSTGRES_PORT=****************

# Airflow Core Settings
AIRFLOW__CORE__EXECUTOR=****************
AIRFLOW__CORE__LOAD_EXAMPLES=****************
AIRFLOW__CORE__SQL_ALCHEMY_CONN=****************
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=****************
AIRFLOW_CONN_POSTGRES_DATA=****************
AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=****************

# Airflow Webserver Settings
AIRFLOW__WEBSERVER__WEB_SERVER_HOST=****************
AIRFLOW__WEBSERVER__WEB_SERVER_PORT=****************
AIRFLOW__WEBSERVER__AUTHENTICATE=****************
AIRFLOW__WEBSERVER__AUTH_BACKEND=****************
AIRFLOW__WEBSERVER__WORKER_CLASS=****************
AIRFLOW__WEBSERVER__SECRET_KEY=****************
AIRFLOW__WEBSERVER__BASE_URL=****************

# Airflow Scheduler Settings
AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL=****************
AIRFLOW__SCHEDULER__MIN_FILE_PROCESS_INTERVAL=****************

# Docker Settings
HOSTNAME=****************
AIRFLOW_IMAGE_NAME=****************

# Django Settings
DJANGO_SETTINGS_MODULE=****************
DJANGO_SECRET_KEY=****************
DJANGO_DEBUG=****************
DJANGO_ALLOWED_HOSTS=****************

# Django Database
DJANGO_DB_NAME=****************
DJANGO_DB_USER=****************
DJANGO_DB_PASSWORD=****************
DJANGO_DB_HOST=****************
DJANGO_DB_PORT=****************

```

## Usage

AWS 에서 EC2 인스턴스을 만들어 다음 명령어를 입력
```cmd
sudo apt update
sudo apt-get install apt-transport-https ca-certificates curl gnupg-agent software-properties-common

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update
sudo apt-get install docker.io
sudo docker-compose up -d --build
sudo systemctl enable docker && service docker start
```

```cmd
본인이 설정한 EC2 환경의 ip주소로 접속
```

## 시스템 아키텍처

### 프로그램의 전체적인 구성 도표 삽입 및 설명

<p>
  <img src="./docs/모델 배포/시스템 구성도/전체 시스템 구성도.png" alt="이미지 설명" width="500" height="350">
</p>

  
 
---

## 수행 결과

> ex ) docs폴더 참조

- **데이터 수집 및 저장**
	- 요구사항정의서
	- 데이터 수집
	- 데이터베이스 설계문서
	- 시나리오설계서
	- 데이터 조회프로그램
	- 프로젝트기획서

- **데이터 전처리**
	- **중간 발표 PPT**
	- **수집된 데이터 및 데이터 전처리 문서**
		- 서울시 매물 데이터
		- 서울시 범죄 통계 데이터
		- 문화시설 및 축제 데이터
		- 서울시 지하철역 데이터

- **모델링 및 평가**
	- 시스템 아키텍처
	- LLM 활용 소프트웨어
	- 테스트 계획 및 결과보고서

- **모델 배포**
	- 요구사항정의서
	- 화면설계서
	- 개발된 LLM 연동 웹 어플리케이션
	- 시스템 구성도
	- 테스트 계획 및 결과 보고서

## 한 줄 소감


### 👨‍💻 김정훈
- airflow를 통해 데이터 수집을 손쉽게 예약하고 운영할 수 있는 방법을 배울 수 있어서 좋았고 docker

### 👨‍💻 김태욱
- React를 처음 사용해봤는데 값진 경험이었습니다. 백엔드와 연결하는 과정이 몹시 힘들었지만 저한테 큰 도움이 되었습니다.

### 👩‍💻 박화랑
- LangGraph, FastApi 등 새로운 라이브러리와 프레임워크를 사용해보는 좋은 기회였습니다. 이번 프로젝트를 통해 프롬프트의 역할이 얼마나 중요한지 체감했고 TAG라는 논문을 알게 되었습니다.

### 👨‍💻 박진효
- CoT, Few-shot Prompting 등 다양한 프롬프트 엔지니어링 기법을 활용해보고 모델의 성능 개선을 위해 여러 가지 방법을 시도해보는 좋은 경험이었습니다.