from typing import TypedDict, Annotated, List, Dict
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage

from utils import llm, db

import json
import os
import yaml

with open(os.path.abspath('./prompts.yaml'), 'r', encoding='utf-8') as file:
    prompts = yaml.safe_load(file)


class RealEstateState(TypedDict): # 그래프의 상태를 정의하는 클래스
    real_estate_type: Annotated[str ,"부동산 유형 (예: 아파트, 상가)"]
    keywordlist: Annotated[List[Dict] ,"키워드 리스트"]
    messages: Annotated[list, add_messages]
    summary: Annotated[str, "길어진 메세지 요약"]
    query_sql: Annotated[str ,"생성된 SQL 쿼리"]
    results: Annotated[List[Dict], "쿼리 결과"]
    answers: Annotated[List[str], "최종 답변 결과"]
    query_answer:Annotated[str, 'answer다듬기']

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
    print("[Filter Node] AI가 질문을 식별했습니다.")
    return {"real_estate_type" : real_estate_type, "messages":messages}

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
    return {"summary": response.content, "messages": delete_messages}

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
    print("=================================")
    print("""[re_questions] 질문이 부동산 관련이 아니거나 제대로 인식되지 않았습니다.
          부동산 관련 질문을 좀 더 자세하게 작성해주시면 답변드리겠습니다!!!""")
    new_question = input("새로운 부동산 질문을 입력해주세요: ")
    print("=================================")
    # 수정된 질문을 state에 업데이트
    return {"messages": new_question}

import json

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
        table = db.get_table_info(table_names=["addresses","sales","property_info", "property_locations","location_distances"])
        prompt = prompt.format(
            table = table,
            top_k=5,
            user_query=state['messages'][-1].content
        )
    else:
        prompt = prompts['base_prompt'] + prompts['rentals_prompt']
        table = db.get_table_info(table_names=["addresses","rentals","property_info", "property_locations","location_distances"])
        prompt = prompt.format(
            table = table,
            top_k=5,
            user_query=state['messages'][-1].content
        )
    
    
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

from langchain_community.tools import QuerySQLDatabaseTool

def run_query(state: RealEstateState) -> RealEstateState:
    
    tool = QuerySQLDatabaseTool(db=db)
    results = tool._run(state["query_sql"])

    if results == '':
        results = '결과값이 없습니다!!! 다시 질문해주세요!'
        return {"results": results}

    return {"results":results}

def generate_response(state: RealEstateState)-> RealEstateState:
    print('[generate_response] 답변 생성중입니다...')
    system_prompt = f"""
    당신은 부동산 추천 전문가이자 세계 지식을 갖춘 AI입니다. 
    주어진 정보와 세계 지식을 결합하여 아래 양식에 맞춰서 사용자의 질문에 답변해주세요.
    구분선 이후 간단한 추천이유도 적어줍니다.
    조회한 결과 매물 데이터 전부를 양식에 맞춰서 나열해줍니다.

    정보: {state['results']}


    ## 출력 양식:
    **매물번호**: {{property_id}}

    **특징**:
    {{특징}}

    ________________________

    **추천 이유**:
    {{추천 이유}}
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