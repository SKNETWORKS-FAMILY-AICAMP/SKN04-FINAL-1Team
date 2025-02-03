"""
ChromaDB 벡터 데이터베이스 관리 모듈.

KoSBERT 모델을 사용하여 질문을 벡터화하고,
ChromaDB에 저장하는 기능을 포함한다.
"""

import json  
import chromadb  
from sentence_transformers import SentenceTransformer 

# ✅ 1️. KoSBERT 모델 로드 (한 번만 로드하여 재사용)
model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS")

# ✅ 2️. ChromaDB 클라이언트 및 컬렉션 생성 (데이터 영구 저장)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="qa_vector_db", metadata={"hnsw:space": "cosine"}
)


def initialize_vector_db(jsonl_file="./data/QA.jsonl"):
    """
    ChromaDB가 비어 있는 경우, JSONL 데이터를 로드하여 벡터 DB에 삽입하는 함수.

    Args:
        jsonl_file (str): JSONL 데이터 파일 경로 (기본값: "./data/QA.jsonl")
    """
    existing_count = collection.count()

    if existing_count > 0:
        print(f"🔹 기존에 {existing_count}개의 벡터 데이터가 존재합니다. 삽입을 건너뜁니다.")
        return

    print("🔹 벡터 DB(Chroma)가 비어 있습니다. 데이터를 삽입합니다...")

    # ✅ 3. JSONL 파일 로드
    with open(jsonl_file, "r", encoding="utf-8") as f:
        data = [json.loads(line) for line in f]

    # ✅ 4. 질문 리스트 추출
    questions = [item["question"] for item in data]

    # ✅ 5. KoSBERT를 사용하여 질문을 벡터화 (Batch 처리로 최적화)
    print("🔹 질문을 벡터화하는 중...")
    embeddings = model.encode(questions, batch_size=32, show_progress_bar=True)

    # ✅ 6. ChromaDB에 벡터 추가
    print("🔹 벡터 데이터를 ChromaDB에 저장하는 중...")
    for idx, (question, embedding) in enumerate(zip(questions, embeddings)):
        collection.add(
            ids=str(idx),  # 🔹 ID를 문자열로 변환하여 저장
            embeddings=embedding.tolist(),  # 🔹 리스트 형태로 변환 후 저장
            metadatas={"question": question, "sql": data[idx]["sql"]}  # 🔹 원본 SQL 데이터 포함
        )

    print("✅ 벡터 DB 데이터 삽입 완료!")
    print(f"✅ 총 {len(questions)}개의 벡터 데이터가 ChromaDB에 저장되었습니다.")
