from nodes import (
    RealEstateState,
    filter_node, re_questions, extract_keywords_based_on_db,
    generate_query, clean_sql_response, run_query, generate_response,
    fiter_router, summarize_conversation, should_summarize
)
from utils import memory
from langgraph.graph import StateGraph, START, END

workflow = StateGraph(RealEstateState)

workflow.add_node("Filter Question", filter_node)
workflow.add_node("Summary", summarize_conversation)
workflow.add_node('Re_Questions', re_questions)
workflow.add_node('Extract_keywords_based_on_db', extract_keywords_based_on_db)
workflow.add_node('Generate_Query', generate_query)
workflow.add_node('Clean_Sql_Response', clean_sql_response)
workflow.add_node('Run_Query', run_query)
workflow.add_node('Generate_Response', generate_response)

workflow.add_conditional_edges(
    "Filter Question",
    fiter_router,
    { 'Pass': "Extract_keywords_based_on_db", 'Fail': 'Re_Questions'}
)

workflow.add_conditional_edges(
    START,
    should_summarize,
    {"summarize_conversation": "Summary", "Filter Question":"Filter Question"}
)

workflow.add_edge("Summary", "Filter Question")
workflow.add_edge("Re_Questions", "Filter Question")
workflow.add_edge("Extract_keywords_based_on_db", "Generate_Query")
workflow.add_edge("Generate_Query", "Clean_Sql_Response")
workflow.add_edge("Clean_Sql_Response", "Run_Query")
workflow.add_edge("Run_Query", "Generate_Response")
workflow.add_edge("Generate_Response", END)

llm_app = workflow.compile(checkpointer=memory)