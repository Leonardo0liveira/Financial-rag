from langchain_core.tools import tool
import time
import chromadb
from chromadb.config import Settings
from typing import List, Dict
from pathlib import Path
import os

# Configurar tokenizers para evitar warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Configurações
CHROMADB_PATH = "./chromadb_storage"
COLLECTION_NAME = "financial_reports"

class SimpleVectorDB:
    """Banco de vetores simplificado usando ChromaDB."""
    
    def __init__(self):
        """Inicializa o cliente ChromaDB."""
        Path(CHROMADB_PATH).mkdir(exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=CHROMADB_PATH,
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )
        
        # Criar/carregar coleção
        try:
            self.collection = self.client.get_collection(
                name=COLLECTION_NAME,
                embedding_function=chromadb.utils.embedding_functions.DefaultEmbeddingFunction()
            )
            print(f"📚 Coleção carregada: {self.collection.count()} documentos")
        except:
            self.collection = self.client.create_collection(
                name=COLLECTION_NAME, 
                embedding_function=chromadb.utils.embedding_functions.DefaultEmbeddingFunction()
            )
            print(f"📚 Nova coleção criada")
    
    def add_documents(self, documents: List[str]) -> Dict:
        """Adiciona documentos à coleção, dividindo em chunks se necessário."""
        try:
            existing_count = self.collection.count()
            all_chunks = []
            all_ids = []
            
            for i, doc in enumerate(documents):
                # Se documento é muito grande (>10k chars), dividir em chunks
                if len(doc) > 10000:
                    chunks = self._split_into_chunks(doc)
                    for j, chunk in enumerate(chunks):
                        all_chunks.append(chunk)
                        all_ids.append(f"doc_{existing_count + i}_chunk_{j}")
                else:
                    all_chunks.append(doc)
                    all_ids.append(f"doc_{existing_count + i}")
            
            self.collection.add(documents=all_chunks, ids=all_ids)
            total_docs = self.collection.count()
            
            print(f"✅ {len(all_chunks)} chunks adicionados. Total: {total_docs}")
            return {"status": "success", "documents_added": len(all_chunks), "total_documents": total_docs}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _split_into_chunks(self, document: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
        """Divide um documento grande em chunks menores com sobreposição."""
        chunks = []
        
        # Extrair título do documento se existir
        lines = document.split('\n')
        title = ""
        content_start = 0
        
        for i, line in enumerate(lines[:5]):
            if '📄' in line:
                title = line.strip()
                content_start = i + 1
                break
        
        # Juntar o conteúdo restante
        content = '\n'.join(lines[content_start:])
        
        # Dividir em chunks
        start = 0
        chunk_num = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Se não é o último chunk, tentar quebrar em uma linha completa
            if end < len(content):
                # Procurar por quebra de linha próxima
                for i in range(end, max(start + chunk_size//2, end - 200), -1):
                    if content[i] == '\n':
                        end = i
                        break
            
            chunk_content = content[start:end].strip()
            
            if chunk_content:
                # Adicionar título se existir + número do chunk
                if title:
                    chunk_title = f"{title} (Parte {chunk_num + 1})"
                else:
                    chunk_title = f"Documento (Parte {chunk_num + 1})"
                
                full_chunk = f"{chunk_title}:\n{chunk_content}"
                chunks.append(full_chunk)
                chunk_num += 1
            
            # Próximo chunk com sobreposição
            start = end - overlap if end > overlap else end
            
            # Evitar loop infinito
            if start >= len(content):
                break
        
        return chunks
    
    def search(self, query: str, k: int = 3) -> List[Dict]:
        """Busca e retorna os chunks mais relevantes."""
        try:
            results = self.collection.query(query_texts=[query], n_results=k)
            
            chunks = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
                    similarity = 1.0 / (1.0 + distance)  # Converter distância para similaridade
                    chunks.append({
                        "content": doc,
                        "similarity": similarity,
                        "rank": i + 1
                    })
            
            return chunks
            
        except Exception as e:
            print(f"Erro na busca: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do banco."""
        return {
            "total_documents": self.collection.count(),
            "collection_name": COLLECTION_NAME,
            "storage_path": CHROMADB_PATH
        }
    
    def clear_collection(self) -> Dict:
        """Limpa todos os documentos da coleção atual."""
        try:
            # Pegar todos os IDs
            all_docs = self.collection.get()
            if all_docs['ids']:
                self.collection.delete(ids=all_docs['ids'])
                return {"status": "success", "message": f"Removidos {len(all_docs['ids'])} documentos"}
            else:
                return {"status": "info", "message": "Coleção já estava vazia"}
        except Exception as e:
            return {"status": "error", "message": f"Erro ao limpar coleção: {str(e)}"}
    
    def reset_database(self) -> Dict:
        """Reseta completamente o banco de dados (remove tudo)."""
        try:
            # Deletar coleção
            self.client.delete_collection(COLLECTION_NAME)
            
            # Recriar coleção vazia
            self.collection = self.client.create_collection(
                name=COLLECTION_NAME,
                embedding_function=chromadb.utils.embedding_functions.DefaultEmbeddingFunction()
            )
            
            return {"status": "success", "message": "Banco de dados resetado completamente"}
        except Exception as e:
            return {"status": "error", "message": f"Erro ao resetar banco: {str(e)}"}

# Instância global
vector_db = SimpleVectorDB()

@tool
def vectorize_financial_reports(reports: List[str]) -> Dict:
    """Indexa relatórios financeiros no banco de vetores."""
    if not reports:
        return {"status": "error", "message": "Nenhum relatório fornecido"}
    return vector_db.add_documents(reports)

@tool  
def semantic_search(query: str, k: int = 3) -> List[Dict]:
    """Realiza busca semântica nos relatórios financeiros."""
    if not query or not query.strip():
        return []
    return vector_db.search(query, k)

@tool
def get_vector_stats() -> Dict:
    """Retorna estatísticas do banco de vetores."""
    return vector_db.get_stats()

@tool
def get_retrieval_metrics() -> Dict:
    """Retorna métricas do sistema de recuperação."""
    stats = vector_db.get_stats()
    return {
        "total_documents": stats["total_documents"],
        "collection_name": stats["collection_name"], 
        "storage_path": stats["storage_path"],
        "status": "active" if stats["total_documents"] > 0 else "empty"
    }

@tool
def clear_vector_database() -> Dict:
    """
    Limpa todos os documentos do banco vetorial.
    
    Remove todos os documentos indexados, mantendo a estrutura do banco.
    Use quando quiser recomeçar com documentos novos.
    
    Returns:
        Status da operação de limpeza
    """
    return vector_db.clear_collection()

@tool  
def reset_vector_database() -> Dict:
    """
    Reseta completamente o banco vetorial.
    
    Remove a coleção inteira e recria do zero.
    Use quando houver problemas de configuração ou corrupção.
    
    Returns:
        Status da operação de reset
    """
    return vector_db.reset_database()

def extract_relevant_info(document: str, query: str) -> str:
    """
    Extrai informações relevantes do documento baseado na query do usuário usando busca semântica.
    
    Args:
        document: Documento completo encontrado
        query: Pergunta do usuário
        
    Returns:
        Informações específicas extraídas
    """
    try:
        # Dividir documento em chunks menores para análise
        document_lines = [line.strip() for line in document.split('\n') if line.strip()]
        
        # Extrair título do documento
        document_title = ""
        for line in document_lines[:3]:
            if '📄' in line or any(word in line.lower() for word in [ 'relatório', 'trimestre']):
                document_title = f"**{line}**"
                break
        
        # Extrair termos-chave da query do usuário para busca flexível
        query_terms = set()
        query_lower = query.lower()
        
        # Adicionar palavras da query (removendo stop words básicas)
        stop_words = {'o', 'a', 'do', 'da', 'de', 'no', 'na', 'em', 'por', 'para', 'com', 'foi', 'ser', 'qual', 'que', 'como'}
        for word in query_lower.split():
            cleaned_word = word.strip('.,?!();:')
            if len(cleaned_word) > 2 and cleaned_word not in stop_words:
                query_terms.add(cleaned_word)
        
        # Scoring de linhas baseado na relevância para a query
        scored_lines = []
        
        for line in document_lines:
            if len(line) < 10:  # Ignorar linhas muito curtas
                continue
                
            line_lower = line.lower()
            score = 0
            
            # Pontuação por termos da query encontrados
            for term in query_terms:
                if term in line_lower:
                    score += 3
                    
            # Bonificação para linhas com valores financeiros
            if any(indicator in line_lower for indicator in ['r$', 'milhões', 'bilhões', '%']):
                score += 2
                
            # Bonificação para linhas com métricas financeiras
            if any(metric in line_lower for metric in ['lucro', 'receita', 'ebitda', 'roe', 'margem', 'patrimônio']):
                score += 2
                
            # Bonificação para linhas com números e períodos
            if any(period in line_lower for period in ['3t25', 'q3', 'trimestre', '2024', '2025']):
                score += 1
                
            if score > 0:
                scored_lines.append((score, line))
        
        # Ordenar por score e pegar as mais relevantes
        scored_lines.sort(key=lambda x: x[0], reverse=True)
        relevant_lines = [f"- {line}" for score, line in scored_lines[:8]]  # Top 8 linhas mais relevantes
        
        # Se não encontrou linhas relevantes, usar fallback inteligente
        if not relevant_lines:
            # Buscar linhas com dados financeiros gerais
            for line in document_lines:
                if any(indicator in line.lower() for indicator in ['r$', '%', 'milhões', 'bilhões']):
                    relevant_lines.append(f"- {line}")
                    if len(relevant_lines) >= 5:
                        break
        
        # Se ainda não encontrou nada, pegar início do documento
        if not relevant_lines:
            for i, line in enumerate(document_lines[1:6]):  # Pular título
                if len(line) > 20:
                    relevant_lines.append(f"- {line}")
        
        # Montar resultado final
        result_parts = []
        
        if document_title:
            result_parts.append(document_title)
            result_parts.append("")
        
        if relevant_lines:
            result_parts.extend(relevant_lines)
        else:
            # Último recurso
            result_parts.append(f"- {document[:300]}...")
        
        return "\n".join(result_parts)
        
    except Exception as e:
        # Em caso de erro, retornar versão truncada
        return f"**Erro na extração:** {str(e)}\n\n{document[:300]}..."
        
    except Exception as e:
        # Em caso de erro, retornar versão truncada
        return document[:300] + "..."

def read_file_content(file_path: str) -> str:
    """
    Lê conteúdo de diferentes tipos de arquivo.
    
    Args:
        file_path: Caminho para o arquivo
        
    Returns:
        Conteúdo do arquivo como string
    """
    try:
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        elif file_path.suffix.lower() == '.md':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        elif file_path.suffix.lower() == '.pdf':
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:  # Verificar se extraiu texto
                            text += extracted + "\n"
                    return text if text.strip() else "⚠️ Não foi possível extrair texto do PDF"
            except ImportError:
                return f"⚠️ PyPDF2 não instalado. Para processar PDFs: pip install PyPDF2"
            except Exception as e:
                return f"⚠️ Erro ao processar PDF: {str(e)}"
                
        elif file_path.suffix.lower() in ['.docx', '.doc']:
            try:
                import docx
                doc = docx.Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            except ImportError:
                return f"⚠️ python-docx não instalado. Para processar Word: pip install python-docx"
                
        else:
            return f"❌ Formato de arquivo não suportado: {file_path.suffix}"
            
    except Exception as e:
        return f"❌ Erro ao ler arquivo {file_path}: {str(e)}"

@tool
def index_documents_from_path(folder_path: str, file_pattern: str = "*.txt") -> Dict:
    """
    Indexa documentos de uma pasta específica.
    
    Args:
        folder_path: Caminho para a pasta com documentos
        file_pattern: Padrão de arquivos (ex: "*.txt", "*.pdf", "*.md")
        
    Returns:
        Resultado da indexação
    """
    try:
        folder = Path(folder_path)
        
        if not folder.exists():
            return {"status": "error", "message": f"Pasta não encontrada: {folder_path}"}
            
        if not folder.is_dir():
            return {"status": "error", "message": f"Caminho não é uma pasta: {folder_path}"}
        
        # Encontrar arquivos
        files = list(folder.glob(file_pattern))
        
        if not files:
            return {"status": "error", "message": f"Nenhum arquivo encontrado com padrão '{file_pattern}' em {folder_path}"}
        
        # Ler conteúdo dos arquivos
        documents = []
        for file_path in files:
            content = read_file_content(file_path)
            documents.append(f"📄 {file_path.name}:\n{content}")
        
        # Indexar no banco vetorial
        result = vector_db.add_documents(documents)
        
        return {
            "status": result["status"] if "status" in result else "success",
            "files_processed": len(files),
            "documents_added": result.get("documents_added", len(documents)),
            "total_documents": result.get("total_documents", 0),
            "files": [f.name for f in files]
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@tool
def financial_reports_retriever_tool(query: str) -> str:
    """
    Retriever direto para relatórios financeiros.
    
    Args:
        query: Pergunta sobre dados financeiros
        
    Returns:
        Chunks mais relevantes encontrados
    """
    try:
        # Buscar chunks relevantes
        chunks = vector_db.search(query, k=3)
        
        if not chunks:
            return f"""**❌ Nenhum resultado encontrado para:** "{query}"

**Sugestões:**
- Carregue documentos usando a interface Streamlit  
- Tente termos como "lucro", "receita", "patrimônio"
- Verifique se há PDFs indexados no sistema"""

        # Pegar o melhor chunk
        best_chunk = chunks[0]
        
        # Limitar o tamanho do conteúdo
        content = best_chunk["content"]
        if len(content) > 1500:
            content = content[:1500] + "..."
            
        return f"""**📊 Informação Encontrada**

**Similaridade:** {best_chunk['similarity']:.1%}

---

{content}

---
*Retriever: ChromaDB com embeddings*"""
        
    except Exception as e:
        return f"❌ Erro no retriever: {str(e)}"