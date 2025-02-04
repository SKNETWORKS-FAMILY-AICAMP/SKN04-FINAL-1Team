from nodes import (
    RealEstateState,
    filter_node, re_questions, find_similar_questions, extract_keywords_based_on_db, clean_response,
    generate_query, clean_sql_response, run_query, no_result_answer, generate_response,
    query_router, fiter_router, summarize_conversation, should_summarize, clean_result_query
)
from utils import memory
from langgraph.graph import StateGraph, START, END

workflow = StateGraph(RealEstateState)

workflow.add_node("Filter Question", filter_node)
workflow.add_node("Summary", summarize_conversation)
workflow.add_node('Re_Questions', re_questions)
workflow.add_node('find_similar_questions', find_similar_questions)
workflow.add_node('Extract_keywords_based_on_db', extract_keywords_based_on_db)
workflow.add_node('Generate_Query', generate_query)
workflow.add_node('Clean_Sql_Response', clean_sql_response)
workflow.add_node('Run_Query', run_query)
workflow.add_node('No_Result_Answer', no_result_answer)
workflow.add_node('Clean_results', clean_result_query)
workflow.add_node('Clean_response', clean_response)
workflow.add_node('Generate_Response', generate_response)

workflow.add_conditional_edges(
    "Filter Question",
    fiter_router,
    { 'Pass': "find_similar_questions", 'Fail': 'Re_Questions'}
)

workflow.add_conditional_edges(
    START,
    should_summarize,
    {"summarize_conversation": "Summary", "Filter Question":"Filter Question"}
)

workflow.add_conditional_edges(
    "Run_Query",
    query_router,
    {"결과없음": "No_Result_Answer", "결과있음":"Clean_results"}
)

workflow.add_edge("Summary", "Filter Question")
workflow.add_edge("Re_Questions", END)
workflow.add_edge("find_similar_questions", "Extract_keywords_based_on_db")
workflow.add_edge("Extract_keywords_based_on_db", "Generate_Query")
workflow.add_edge("Generate_Query", "Clean_Sql_Response")
workflow.add_edge("Clean_Sql_Response", "Run_Query")
workflow.add_edge("No_Result_Answer", END)
workflow.add_edge("Clean_results", "Clean_response")
workflow.add_edge("Clean_response", "Generate_Response")
workflow.add_edge("Generate_Response", END)

llm_app = workflow.compile(checkpointer=memory)