from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Body
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
from edges import llm_app
from utils import config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 필요한 도메인 추가
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/real_estate")
async def real_estate_info():
    return {"info": "API는 부동산 관련 요청을 처리할 준비가 되었습니다"}

# 스트리밍 응답 함수
async def stream_llm_response(query_text: str):
    try:
        for chunk in llm_app.stream({'messages': query_text}, config=config, stream_mode="messages"):
            if chunk[1]['langgraph_node'] == "Re_Questions":
                yield chunk[0].content + ""
            if chunk[1]['langgraph_node'] == "No_Result_Answer":
                yield chunk[0].content + ""
            if chunk[1]['langgraph_node'] == "Generate_Response":
                yield chunk[0].content + ""

    except Exception as e:
        yield f"Error: {str(e)}\n"
                

# POST 요청: 사용자 입력 받아 AI 모델에 전달 (스트리밍 방식)
@app.post("/real_estate")
async def handle_real_estate_input(payload: dict = Body(...)):
    query_text = payload.get("query", "")
    if not query_text:
        return {"error": "Invalid input: 'query' is required."}
    
    print(f"Received query: {query_text}")
    return StreamingResponse(stream_llm_response(query_text), media_type="text/plain")

@app.post("/real_estate/coordinates")
async def get_real_estate_coordinates(payload: dict = Body(...)):
    """
    1) query를 입력받아서 전체 파이프라인(또는 필요한 노드)을 거쳐
    2) 최종 state['clean_results']를 생성한 다음
    3) 그 안에서 property_id 및 좌표 데이터를 뽑아서 반환
    """
    query_text = payload.get("query", "")
    if not query_text:
        return JSONResponse(
            status_code=400, 
            content={"error": "Invalid input: 'query' is required."}
        )

    print(f"Received query for coordinates extraction: {query_text}")

    # 1) 실제 파이프라인 실행:
    #    - llm_app.run() 이나 필요한 함수를 호출하여 최종 state를 얻는다고 가정합니다.
    #    - messages 구조는 LangChain/LangGraph에서 사용하는 형태에 맞게 구성해야 합니다.
    # 예시로 HumanMessage(content=query_text)를 전달
    # (사용 중인 메시지 객체가 다를 수 있으니, 실제 구조에 맞게 조정하세요)
    final_state = llm_app.invoke({"messages": query_text}, config=config)

    # 2) 파이프라인 실행 결과, clean_result_query 노드 등에서 'clean_results'가 채워졌다고 가정
    clean_results = final_state.get("clean_results", "")

    # 만약 clean_results가 비어있다면 에러 처리
    if not clean_results:
        return JSONResponse(
            status_code=404, 
            content={"error": "No clean_results found in final state."}
        )

    # 3) clean_results(JSON 문자열)에서 property_id와 coordinates를 추출
    try:
        data = json.loads(clean_results)
        property_id = data.get("property_id")
        coordinates = data.get("coordinates")

        return {
            "property_id": property_id,
            "coordinates": coordinates
        }
    except json.JSONDecodeError as e:
        return JSONResponse(
            status_code=500, 
            content={"error": f"JSON parse error: {str(e)}"}
        )
