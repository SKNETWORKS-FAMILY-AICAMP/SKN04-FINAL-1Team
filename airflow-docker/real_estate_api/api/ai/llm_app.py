from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.messages import HumanMessage, AIMessage, SystemMessage
import yaml
import os

def load_prompts():
    with open(os.path.join(os.path.dirname(__file__), 'prompts.yaml'), 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def create_chain(config):
    prompts = load_prompts()
    
    llm = ChatOpenAI(
        model_name=config.get("model_name", "gpt-4-turbo-preview"),
        temperature=config.get("temperature", 0.7),
        streaming=True,
        openai_api_key=config.get("openai_api_key")
    )
    
    template = prompts['base_prompt']
    prompt = ChatPromptTemplate.from_messages([
        ("system", template),
        ("human", "{message}"),
        ("system", "데이터베이스 스키마:\n{table}")
    ])
    
    chain = (
        prompt
        | llm
        | StrOutputParser()
    )
    
    return chain

def stream_response(query, config=None):
    if config is None:
        from .config import config
    chain = create_chain(config)
    
    for chunk in chain.stream({
        "message": query.get("message", ""),
        "table": query.get("table", "")
    }):
        # 응답을 생성하는 노드로 처리
        yield (
            AIMessage(content=chunk),
            {"langgraph_node": "Generate_Response"}
        ) 