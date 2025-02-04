from typing import TypedDict, Annotated, List, Dict
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool

from utils import llm
from postgresql import db
from chroma_db import model, collection, initialize_vector_db

import json
import os
import yaml
import re

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
    properties: Annotated[List[Dict], "부동산 정보"]

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

    previous_message = state["messages"][-2].content if len(state["messages"]) > 1 else ""  # ✅ 직전 메시지

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
        return {"real_estate_type" : real_estate_type, "messages":messages}

    return {"real_estate_type" : real_estate_type}

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

def find_similar_questions(state: RealEstateState) -> RealEstateState:
    """
    사용자의 질문을 벡터화하여 ChromaDB에서 유사한 질문을 검색.
    threshold 값보다 높은(유사한) 결과만 반환.
    """
    initialize_vector_db()  # ✅ 벡터 DB 초기화

    query = state["messages"][-1].content  # ✅ 최신 입력된 사용자 메시지
    top_k = 5  # 검색할 유사 질문 개수
    threshold = 0.7  # ✅ 코사인 유사도 기준 (1에 가까울수록 유사)

    # ✅ 입력된 질문을 벡터화
    query_embedding = model.encode([query])[0].tolist()

    # ✅ ChromaDB에서 유사 질문 검색
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    # ✅ 유사도 변환 및 필터링 (코사인 유사도 사용)
    filtered_results = [
        {
            "score": 1 - score,  # ✅ 코사인 거리 → 코사인 유사도로 변환 (1 - 거리)
            "full_question": doc.get("question"),
            "sql": doc.get("sql")
        }
        for doc, score in zip(results["metadatas"][0], results["distances"][0])
        if (1 - score) >= threshold  # ✅ 유사도 기준 필터링 (0.7 이상만 출력)
    ]

    # ✅ 검색 결과 출력
    if not filtered_results:
        print("❌ 유사한 질문이 없습니다.")
        return {"vector_results": "❌ 유사한 질문이 없습니다."}

    else:
        for i, res in enumerate(filtered_results):
            print(f"🔍 [{i+1}] 유사도 점수: {res['score']:.4f}")  # ✅ 변환된 유사도 출력
            print(f"📌 원본 질문: {res['full_question']}")
            print(f"📝 연관 SQL: {res['sql']}\n")

    return {"vector_results": filtered_results}  # ✅ 필터링된 유사 질문 반환


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

    keywordlist = state['keywordlist']

    if keywordlist['Transaction Type'] == '매매':
        prompt = prompts['base_prompt'] + prompts['sales_prompt']
        transaction_type = 'sales'
        
    else:
        prompt = prompts['base_prompt'] + prompts['rentals_prompt']
        transaction_type = 'rentals'
        
    table = db.get_table_info(table_names=[
        "addresses",
        transaction_type,
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
        examples = "\n".join(
            [
                f"- **질문:** {res['full_question']}\n  **SQL:** `{res['sql']}`"
                for res in state['vector_results']
            ]
        )
        prompt = prompt + f"\n\n**유사한 질문 예시:**\n{examples}"
    
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
    base_prompt = prompts['clean_result_base_prompt']

    keywordlist = state['keywordlist']

    if keywordlist['Transaction Type'] == '전세' or keywordlist['Transaction Type'] == '없음':
        clean_result_query_prompt = base_prompt + prompts['clean_result_yearly_rental_prompt']
    
    elif keywordlist['Transaction Type'] == '월세':
        clean_result_query_prompt = base_prompt + prompts['clean_result_monthly_rental_prompt']
    
    else:
        clean_result_query_prompt = base_prompt + prompts['clean_result_sale_prompt']
        
    user_prompt=f"{state['results']}"

    response = llm.invoke([
            SystemMessage(content=clean_result_query_prompt),
            HumanMessage(content=user_prompt)
        ])
    
    output = response.content.strip()

    return {"clean_results":output}

# ✅ 전역 변수로 최신 properties 저장
latest_properties = []

def clean_response(state: RealEstateState) -> RealEstateState:
    global latest_properties
    print('[clean_response]: 쿼리문을 다듬는 중 입니다.')

    clean_results = state['clean_results']

    # ```json ``` 제거
    if clean_results.startswith("```json") and clean_results.endswith("```"):
        clean_results = clean_results[7:-3].strip()

    # None, NaN, Infinity 변환
    clean_results = clean_results.replace("None", "null").replace("NaN", "0").replace("Infinity", "0")

    # 역슬래시 제거
    clean_results = re.sub(r'\\(?!["\\/bfnrtu])', '', clean_results)

    # 키-값 자동 수정 (": "가 없는 경우)
    clean_results = re.sub(r"(\w+):", r'"\1":', clean_results)

    print(f"💡 JSON 데이터 확인:\n{clean_results}")

    try:
        data_list = json.loads(clean_results)

        if not isinstance(data_list, list):
            print(f"❌ JSON 데이터가 리스트가 아님: {type(data_list)}")
            raise ValueError("JSON 데이터가 리스트가 아닙니다.")

        latest_properties.clear()
        latest_properties.extend([
            {
                "property_id": item.get("property_id"),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude")
            }
            for item in data_list
        ])

        print(f"✅ Updated properties: {latest_properties}")

        return {"properties": latest_properties}

    except json.JSONDecodeError as e:
        print(f"🚨 JSON 파싱 오류 발생: {e}")
        print(f"💡 JSON 데이터 확인:\n{clean_results}")
        return {"properties": []}  # 오류 발생 시 빈 리스트 반환

def generate_response(state: RealEstateState)-> RealEstateState:
    print('[generate_response] 답변 생성중입니다...')

    data = state['clean_results']
    keywordlist = state['keywordlist']

    if keywordlist['Transaction Type'] == '전세' or keywordlist['Transaction Type'] == '없음':
        money_info = "**💰 보증금:** [보증금]"
    
    elif keywordlist['Transaction Type'] == '월세':
        money_info = "**💰 보증금:** [보증금]\n- **💰 월세:** [월세]"
    
    else:
        money_info = "**💰 가격:** [가격]"

    generate_response_prompt = prompts['generate_response_prompt'].format(money_info=money_info, data=data)

    user_prompt=f"""
    사용자의 질문: {state['messages'][-1].content}
    """
    response = llm.invoke([
            SystemMessage(content=generate_response_prompt),
            HumanMessage(content=user_prompt)
        ])
    
    output = response.content.strip()

    return {'answers': output}