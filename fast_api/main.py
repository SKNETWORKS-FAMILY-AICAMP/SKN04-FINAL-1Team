from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Body
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from edges import llm_app
from nodes import latest_properties
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

async def stream_llm_response(query_text: str):
    try:
        for chunk in llm_app.stream({'messages': query_text}, config=config, stream_mode="messages"):
            # 🚀 각 응답을 일정 시간마다 출력하도록 딜레이 추가 (예: 0.5초)

            if chunk[1]['langgraph_node'] == "Re_Questions":
                yield chunk[0].content + ""
            elif chunk[1]['langgraph_node'] == "No_Result_Answer":
                yield chunk[0].content + ""
            elif chunk[1]['langgraph_node'] == "Generate_Response":
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

@app.get("/properties")
async def get_properties():
    global latest_properties
    if not latest_properties:
        return JSONResponse(content={"error": "No properties available yet"}, status_code=404)

    return JSONResponse(content={"properties": latest_properties})