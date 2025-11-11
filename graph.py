from langgraph.graph import END, StateGraph, START
from langgraph.checkpoint.memory import MemorySaver

from agent_state import AgentState
from nodes import (
    agent, 
    should_continue, 
    should_summarize, 
    summarize_conversation,
    financial_tool_node
)

import os

# =============================================================================
# SIMPLE FINANCIAL RAG GRAPH  
# =============================================================================

# Graph simplificado - apenas Financial RAG
builder = StateGraph(AgentState)

# Nós principais
builder.add_node("summarize_conversation", summarize_conversation)
builder.add_node("agent", agent)
builder.add_node("financial_tools", financial_tool_node)

# Fluxo inicial - verificar se precisa resumir
builder.add_conditional_edges(
    START, 
    should_summarize,
    {
        "summarize_conversation": "summarize_conversation",
        "agent": "agent"
    }
)

# Sempre voltar para o agente após resumir
builder.add_edge("summarize_conversation", "agent")

# Do agente, verificar se deve usar ferramentas ou terminar
builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "financial_tools",
        "end": END,
    }
)

# Após usar ferramentas, terminar
builder.add_edge("financial_tools", END)

# Compilar o graph
graph = builder.compile(checkpointer=MemorySaver())