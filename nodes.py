from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, SystemMessage, RemoveMessage
from langgraph.prebuilt import ToolNode

from config import llm
from agent_state import AgentState
from prompts import RAG_FORMATTER_PROMPT, FINANCIAL_AGENT_PROMPT
from tools import (
    financial_reports_retriever_tool,
    vectorize_financial_reports,
    semantic_search,
    get_retrieval_metrics
)

# Remover CustomToolNode - usar ToolNode padrão

# Configuração
financial_agent_msg = SystemMessage(content=FINANCIAL_AGENT_PROMPT)
tools = [financial_reports_retriever_tool]
llm_with_tools = llm.bind_tools(tools)

# =============================================================================
# NODES PRINCIPAIS  
# =============================================================================

def should_summarize(state: AgentState):
    """Decide se deve resumir a conversa."""
    messages = state["messages"]
    return "summarize_conversation" if len(messages) > 5 else "agent"

def summarize_conversation(state: AgentState):
    """Resume a conversa quando muito longa."""
    summary = state.get("summary", "")
    if summary:
        summary_message = (
            f"Resumo atual: {summary}\\n\\n"
            "Atualize o resumo com as novas mensagens:"
        )
    else:
        summary_message = "Crie um resumo da conversa:"
        
    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = llm.invoke(messages)
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-5]]
    return {"summary": response.content, "messages": delete_messages}

def agent(state: AgentState):
    """Agente principal que processa mensagens."""
    summary = state.get("summary", "")
    if summary:
        summary_text = f"Resumo da conversa: {summary}"
        messages = [AIMessage(content=summary_text)] + state["messages"]
    else:
        messages = state["messages"]
    
    return {"messages": [llm_with_tools.invoke([financial_agent_msg] + messages)]}

def should_continue(state: AgentState):
    """Decide se deve continuar ou terminar."""
    messages = state["messages"]
    last_message = messages[-1]
    return "continue" if last_message.tool_calls else "end"

def grade_documents(state: AgentState):
    """Passa documentos sem filtro adicional (simplificado)."""
    return {
        "docs": state.get("docs", []), 
        "query": state.get("query", ""), 
        "index": state.get("index", "")
    }

def generate(state: AgentState):
    """Gera resposta final baseada nos documentos recuperados."""
    docs = state.get("docs", [])
    messages = state.get("messages", [])
    retrieved_doc = state.get("retrieved_doc", "")
    similarity_score = state.get("similarity_score", 0.0)
    confidence = state.get("confidence", "baixa")
    
    if retrieved_doc:
        # Sistema RAG financeiro
        prompt = RAG_FORMATTER_PROMPT.format(
            retrieved_doc=retrieved_doc,
            query=state.get("query", ""),
            confidence=confidence,
            similarity_score=similarity_score
        )
        response = llm.invoke([SystemMessage(content=prompt)] + messages)
    elif docs:
        # Sistema tradicional (fallback)
        docs_string = "\\n".join([f"Documento: {doc.page_content}" for doc in docs])
        prompt = f"Baseado nos documentos: {docs_string}\\n\\nResponda à pergunta do usuário."
        response = llm.invoke([SystemMessage(content=prompt)] + messages)
    else:
        response = AIMessage(content="Não encontrei informações suficientes para responder.")
   
    return {"messages": [response]}

# =============================================================================
# NODES RAG FINANCEIRO
# =============================================================================

def vectorize_reports(state: AgentState):
    """Vetoriza relatórios financeiros de exemplo."""
    result = vectorize_financial_reports.invoke({"reports": SAMPLE_FINANCIAL_REPORTS})
    
    return {
        "query": state.get("query", ""),
        "financial_reports": SAMPLE_FINANCIAL_REPORTS,
        "vector_db_info": result
    }

def semantic_retrieve(state: AgentState):
    """Realiza busca semântica.""" 
    query = state.get("query", "")
    if not query:
        return {"retrieved_doc": "", "similarity_score": 0.0, "confidence": "baixa"}
    
    result = semantic_search.invoke({"query": query})
    
    return {
        "query": query,
        "retrieved_doc": result["document"],
        "similarity_score": result["similarity_score"],
        "confidence": result["confidence"],
        "retrieval_metrics": {"retrieval_time": result["retrieval_time"]}
    }

def confidence_grade(state: AgentState):
    """Avalia confiança do resultado."""
    similarity_score = state.get("similarity_score", 0.0)
    
    if similarity_score > 0.8:
        confidence = "alta"
        grade = "A"
    elif similarity_score > 0.6:
        confidence = "média" 
        grade = "B"
    else:
        confidence = "baixa"
        grade = "C"
    
    return {
        "confidence": confidence,
        "confidence_grade": grade,
        "similarity_score": similarity_score
    }

# =============================================================================
# TOOL NODES  
# =============================================================================

# Usar ToolNode padrão do LangGraph
tool_node = ToolNode(tools)
financial_tools = [financial_reports_retriever_tool] 
financial_tool_node = ToolNode(financial_tools)