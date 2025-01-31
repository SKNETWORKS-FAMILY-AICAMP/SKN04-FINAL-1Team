from typing import TypedDict, Annotated, List, Dict
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool

from utils import llm
from database import insert_data_if_empty, db, model, collection

import json
import os
import yaml

with open(os.path.abspath('./prompts.yaml'), 'r', encoding='utf-8') as file:
    prompts = yaml.safe_load(file)

class RealEstateState(TypedDict): # 그래프의 상태를 정의하는 클래스
    real_estate_type: Annotated[str ,"부동산 유형 (예: 아파트, 상가)"]
    vector_results: Annotated[str, "벡터 결과"]
    keywordlist: Annotated[List[Dict] ,"키워드 리스트"]
    messages: Annotated[list, add_messages]
    summary: Annotated[str, "길어진 메세지 요약"]
    query_sql: Annotated[str ,"생성된 SQL 쿼리"]
    results: Annotated[List[Dict], "쿼리 결과"]
    query_answer:Annotated[str, 'answer다듬기']
    answers: Annotated[List[str], "최종 답변 결과"]
    clean_results: Annotated[List[Dict], "결과 정제"]

def filter_node(state:RealEstateState) -> RealEstateState:
    print("[Filter Node] AI가 질문을 식별중입니다!!!!")
    system_prompt = prompts['filter_system_prompt']

    summary = state.get("summary", "")
    if summary:

        # Add summary to system message
        summary_message = f"Summary of conversation earlier: {summary}"

        # Append summary to any newer messages
        messages = summary_message + state["messages"][-1].content

    else:
        messages = state["messages"][-1].content

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(messages)
    ])

    real_estate_type = response.content.strip() 

    print(f"[Filter Node] AI가 질문을 식별했습니다. {real_estate_type}")

    previous_message = messages[-2] if len(messages) > 1 else ""  # ✅ 직전 메시지

    # ✅ 만약 최근 질문이 부동산과 관련 없으면 직전 질문과 연결 가능 여부 확인
    if real_estate_type == "Fail" and previous_message:
        print("[Filter Node] 최근 질문이 애매해서 직전 질문과 연결 여부 검사 중...")
        
        combined_message = previous_message + " " + messages
        combined_response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(combined_message)
        ])
        
        combined_real_estate_type = combined_response.content.strip()
        print(f"[Filter Node] 직전 질문과 결합 시: {combined_real_estate_type}")

        # ✅ 직전 질문과 합쳤을 때 부동산 관련이면 유지
        if combined_real_estate_type != "Fail":
            real_estate_type = combined_real_estate_type 

    return {"real_estate_type" : real_estate_type,
            "messages":messages,
            "re_question": False
            }

def summarize_conversation(state: RealEstateState):
    summary = state.get("summary", "")
    if summary:
        summary_prompt = (
            f"현재까지의 대화 요약: {summary}\n\n"
            "위의 새로운 메시지를 고려하여 요약을 확장하세요:"
        )
    else:
        summary_prompt = "위의 대화를 요약하세요:"

    messages = state["messages"] + [HumanMessage(content=summary_prompt)]
    response = llm.invoke(messages)

    # 최근 2개의 메시지만 남기고 이전 메시지 삭제
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content, "messages": delete_messages,}

def should_summarize(state: RealEstateState) :
    if len(state["messages"]) > 6:
        return "summarize_conversation"
    return "Filter Question"

def fiter_router(state: RealEstateState):
    # This is the router
    real_estate_type = state["real_estate_type"]
    if real_estate_type == "Pass":
        return "Pass"
    else:
        return 'Fail'
    
def re_questions(state: RealEstateState) -> RealEstateState:
    system_prompt = """
    모든 질문에 대해 아래의 문구로만 답변하세요:

    "❌부동산 관련 질문을 다시 입력해주세요!🏠"

    # Output Format
    - 항상 위의 메시지를 사용하여 단일 문장으로 응답하십시오.

    """

    user_prompt=f"""
    사용자의 질문: {state['messages'][-1].content}
    """
    response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
    
    output = response.content.strip()

    return {'answers': output}

def search_similar_questions(state: RealEstateState):  
    """
    사용자의 질문을 벡터화하여 ChromaDB에서 유사한 질문을 검색.
    threshold 값보다 낮은(유사한) 결과만 반환.
    예시로 사용 예정
    """

    insert_data_if_empty()  # 데이터베이스에 데이터가 없으면 삽입

    query = state["messages"][-1].content
    top_k = 5
    threshold = 0.5

    query_embedding = model.embed_documents([query])[0]  # 입력 문장 벡터화
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    
    filtered_results = [
        {"score": score, "full_question": doc.get("full_question"), "sql": doc.get("sql")}
        for doc, score in zip(results["metadatas"][0], results["distances"][0])
        if score < threshold  # 쓰레쉬홀드(임계값) 적용
    ]

    # 검색 결과 출력
    if not filtered_results:
        print("❌ 유사한 질문이 없습니다.")
        return {"vector_results" : "❌ 유사한 질문이 없습니다."}

    else:
        for i, res in enumerate(filtered_results):
            print(f"🔍 [{i+1}] Score: {res['score']:.4f}")
            print(f"📌 Question: {res['full_question']}")
            print(f"📝 SQL: {res['sql']}\n")

    return {"vector_results":filtered_results}  # 필터링된 문서 반환

def extract_keywords_based_on_db(state: RealEstateState) -> RealEstateState:
    system_prompt = prompts['keyword_system_prompt']

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["messages"][-1].content)
    ])
    
    extracted_keywords = response.content.strip()
    result = json.loads(extracted_keywords)
    return {"keywordlist":result}

def generate_query(state: RealEstateState) -> RealEstateState:

    print("[generate_query] 열심히 데이터베이스 쿼리문을 작성중입니다...")

    if state['keywordlist'] == '매매':
        prompt = prompts['base_prompt'] + prompts['sales_prompt']
        keywordlist = 'sales'
        
    else:
        prompt = prompts['base_prompt'] + prompts['rentals_prompt']
        keywordlist = 'rentals'
        
    table = db.get_table_info(table_names=[
        "addresses",
        keywordlist,
        "property_info",
        "property_locations",
        "location_distances",
        "cultural_facilities",
    ])

    prompt = prompt.format(
            table = table,
            top_k=5,
            user_query=state['messages'][-1].content
        )
    
    if state['vector_results'] != '❌ 유사한 질문이 없습니다.':    
        prompt = prompt + f"**유사한 질문 예시**:\n{state['vector_results']}"
    
    response = llm.invoke([
            SystemMessage(content="당신은 SQLite Database  쿼리를 생성하는 전문가입니다."),
            HumanMessage(prompt)
        ])
    
    print('[generate_query]: 쿼리문을 생성했습니다!')
    
    return {"query_sql":response.content}

def clean_sql_response(state: RealEstateState) -> RealEstateState:
    print('[clean_sql_response]: 쿼리문을 다듬는 중 입니다.')
    
    # 'query_sql' 키는 항상 존재한다고 가정
    query_sql = state['query_sql']

    # 코드 블록(````sql ... `````) 제거
    if query_sql.startswith("```sql") and query_sql.endswith("```"):
        query_sql = query_sql[6:-3].strip()  # "```sql" 제거 후 앞뒤 공백 제거

    # SQL 문 끝에 세미콜론 추가 (필요시)
    if not query_sql.strip().endswith(";"):
        query_sql = query_sql.strip() + ";"
        
    print('[clean_sql_response]: 쿼리문 다듬기 끝.')
    # 상태 업데이트
    return {"query_sql":query_sql}

def run_query(state: RealEstateState) -> RealEstateState:
    
    tool = QuerySQLDataBaseTool(db=db)
    results = tool._run(state["query_sql"])

    if results == '':
        results = '결과없음'
        return {"results": results}

    return {"results":results}

def query_router(state: RealEstateState):
    # This is the router
    results = state["results"]
    if results == "결과없음":
        return "결과없음"
    else:
        return '결과있음'
    
def no_result_answer(state: RealEstateState) -> RealEstateState:
    query = state['messages'][-1].content

    no_result_answer_prompt = prompts['no_result_answer_prompt'].format(query=query)

    user_prompt = f"사용자 질문:{query}"
    response = llm.invoke([
            SystemMessage(content=no_result_answer_prompt),
            HumanMessage(content=user_prompt)
        ])
    
    output = response.content.strip()

    return {'answers': output}

def clean_result_query(state: RealEstateState) -> RealEstateState:
    clean_result_query_prompt = prompts['clean_result_query_prompt']
        
    user_prompt=f"{state['results']}"

    response = llm.invoke([
            SystemMessage(content=clean_result_query_prompt),
            HumanMessage(content=user_prompt)
        ])
    
    output = response.content.strip()

    return {"clean_results":output}

def generate_response(state: RealEstateState)-> RealEstateState:
    print('[generate_response] 답변 생성중입니다...')

    data = state['clean_results']

    generate_response_prompt = prompts['generate_response_prompt'].format(data=data)

    user_prompt=f"""
    사용자의 질문: {state['messages'][-1].content}
    """
    response = llm.invoke([
            SystemMessage(content=generate_response_prompt),
            HumanMessage(content=user_prompt)
        ])
    
    output = response.content.strip()

    return {'answers': output}