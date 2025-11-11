from typing import Annotated, TypedDict, List, Dict, Optional, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
import numpy as np

#STATE
class AgentState(TypedDict):
    """
    Financial Reports RAG Agent State
    
    Messages: para armazenar histórico de interações
    Query: Pergunta do usuário
    Index: para identificar base de conhecimento aplicada
    Docs: lista de documentos recuperados e filtrados
    Summary: resumo da conversa
    
    Novos campos para RAG:
    Financial_reports: relatórios financeiros para indexação
    Vectors: vetores TF-IDF/Word2Vec dos documentos
    Retrieved_doc: documento mais similar recuperado
    Similarity_score: pontuação de similaridade
    Confidence: nível de confiança (alta/média/baixa)
    Retrieval_metrics: métricas de performance do sistema
    Vector_db_info: informações sobre o banco de vetores persistente
    """

    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    index: str
    docs: List[Dict]
    summary: str
    
    # Campos para Financial Reports RAG
    financial_reports: Optional[List[str]]
    vectors: Optional[Any]  # numpy array ou matriz esparsa
    retrieved_doc: Optional[str]
    similarity_score: Optional[float]
    confidence: Optional[str]  # "alta", "média", "baixa"
    retrieval_metrics: Optional[Dict[str, float]]
    
    # Campos para banco de vetores persistente
    vector_db_info: Optional[Dict[str, Any]]  # tipo de DB, path, estatísticas


class ConfidenceGrade(BaseModel):
    """
    Avalia o nível de confiança baseado na similaridade semântica.
    Classifica a confiança em alta (>0.75), média (0.5-0.75) ou baixa (<0.5).
    """
    
    confidence_level: str = Field(
        description="Nível de confiança: 'alta', 'média' ou 'baixa'"
    )
    similarity_score: float = Field(
        description="Pontuação de similaridade entre 0 e 1"
    )

class RetrievalMetrics(BaseModel):
    """
    Métricas para avaliação do sistema RAG.
    """
    
    semantic_precision: Optional[float] = Field(
        description="Proporção de documentos com similaridade > 0.6"
    )
    retrieval_latency: Optional[float] = Field(
        description="Tempo médio de busca em milissegundos"
    )
    confidence_distribution: Optional[Dict[str, int]] = Field(
        description="Distribuição dos níveis de confiança"
    )
