from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Body
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
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
