from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langchain_openai.chat_models.base import ChatOpenAI

from dotenv import load_dotenv
from langsmith import Client

load_dotenv() 
client = Client() # langsmith 추적

config = RunnableConfig(
    recursion_limit=25,  # 최대 25개개 노드까지 방문. 그 이상은 RecursionError 발생
    configurable={"thread_id": "1"},  # 스레드 ID 설정, ssesion_id랑 연결해서 사용 예정
    tags=["랭그래프설계(5)"],  # Tag, 없어도 됨
)
memory = MemorySaver()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=1)

