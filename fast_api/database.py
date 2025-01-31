from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from langchain_community.utilities import SQLDatabase

import json
import chromadb

from langchain_openai.embeddings import OpenAIEmbeddings

def get_db_engine(user, password, host, port, database):
    """PostgreSQL DB와 연결된 엔진을 생성합니다."""
    try:
        # SQLAlchemy 엔진 생성 (PostgreSQL)
        engine = create_engine(
            f"postgresql://{user}:{password}@{host}:{port}/{database}",
            poolclass=NullPool  # 커넥션 풀링 비활성화 (단일 연결 사용)
        )
        return engine
    except Exception as e:
        print(f"데이터베이스 연결 중 오류 발생: {str(e)}")
        return None

# PostgreSQL 접속 정보
DB_CONFIG = {
    "user": "postgres",     # PostgreSQL 사용자 이름
    "password": "1234", # PostgreSQL 비밀번호
    "host": "localhost",         # PostgreSQL 서버 주소 (Docker 사용 시 컨테이너 이름 가능)
    "port": "5432",              # PostgreSQL 포트 (기본 5432)
    "database": "real_estate"    # 사용할 데이터베이스 이름
}

# PostgreSQL 엔진 생성
engine = get_db_engine(**DB_CONFIG)

# LangChain SQLDatabase 객체 생성
db = SQLDatabase(
    engine,
    sample_rows_in_table_info=False  # 샘플 행 조회 비활성화
)


# 1️⃣ 벡터 임베딩 모델 로드
model = OpenAIEmbeddings(model="text-embedding-3-small")

# 2️⃣ ChromaDB 인스턴스 생성
chroma_client = chromadb.PersistentClient(path="./chroma_db")  # 영구 저장
collection = chroma_client.get_or_create_collection(name="jsonl_vectors")

# 3️⃣ 질문을 띄어쓰기 기준으로 분할하여 저장하는 함수
def chunk_text(text):
    chunks = text.split()
    return chunks

# 4️⃣ 기존 데이터 확인 후, 벡터DB가 없을 경우 데이터 삽입
def insert_data_if_empty(jsonl_file="./data/QA.jsonl"):
    existing_count = collection.count()

    if existing_count == 0:
        print("🔹 벡터 DB가 비어 있습니다. 데이터를 삽입합니다...")

        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)  # JSON 객체 변환
                question = data.get("question")  # 질문 (Query)
                sql = data.get("sql")  # SQL 문장

                if question and sql:
                    # 질문을 여러 청크로 나누어 저장 (n-gram 방식)
                    chunks = chunk_text(question)
                    for chunk in chunks:
                        embedding = model.embed_documents([chunk])[0]  # 청크를 벡터화
                        collection.add(
                            ids=[str(len(collection.get()["ids"]))],  # 고유 ID 자동 생성
                            embeddings=[embedding],
                            metadatas=[{"question": chunk, "full_question": question, "sql": sql}]  # 원본 데이터 저장
                        )

        print("✅ 데이터 삽입 완료!")
    else:
        print(f"🔹 기존에 {existing_count}개의 벡터 데이터가 존재합니다. 삽입을 건너뜁니다.")
