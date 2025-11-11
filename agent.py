from uuid import uuid1
import streamlit as st
from graph import graph

def run(text, config):  
    return graph.invoke({"messages": text}, config, debug=True)  


def build_page(is_on: bool):
    if "thread_id" not in st.session_state:
        st.session_state["thread_id"] = str(uuid1())

    if is_on:  
        st.title("Financial Reports RAG — Sistema de Recuperação Semântica")
        
        # Sidebar com controles e métricas
        with st.sidebar:
            st.header("� Gerenciar Documentos")
            
            # Upload de arquivos
            uploaded_files = st.file_uploader(
                "Upload de Relatórios Financeiros",
                type=['txt', 'pdf', 'docx', 'md'],
                accept_multiple_files=True,
                help="Formatos suportados: TXT, PDF, DOCX, MD"
            )
            
            # Processamento automático quando arquivos são enviados
            if uploaded_files and "last_uploaded_files" not in st.session_state:
                st.session_state["last_uploaded_files"] = []
            
            # Verificar se há novos arquivos
            if uploaded_files:
                current_files = [f.name for f in uploaded_files]
                if current_files != st.session_state.get("last_uploaded_files", []):
                    st.session_state["last_uploaded_files"] = current_files
                    
                    # Auto-indexar novos arquivos
                    with st.spinner("🔄 Auto-indexando arquivos..."):
                        try:
                            from tools import vectorize_financial_reports
                            import tempfile
                            import os
                            
                            documents = []
                            processed_count = 0
                            
                            for uploaded_file in uploaded_files:
                                try:
                                    # Criar arquivo temporário
                                    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
                                        tmp_file.write(uploaded_file.getvalue())
                                        tmp_path = tmp_file.name
                                    
                                    # Processar arquivo
                                    from tools import read_file_content
                                    content = read_file_content(tmp_path)
                                    
                                    if "❌ Erro" not in content and "não suportado" not in content:
                                        documents.append(f"📄 {uploaded_file.name}:\n{content}")
                                        processed_count += 1
                                    
                                    # Limpar arquivo temporário
                                    os.unlink(tmp_path)
                                    
                                except Exception as e:
                                    st.error(f"Erro processando {uploaded_file.name}: {str(e)}")
                            
                            # Indexar documentos
                            if documents:
                                result = vectorize_financial_reports.invoke({"reports": documents})
                                if result["status"] == "success":
                                    st.success(f"✅ {processed_count} documentos indexados automaticamente!")
                                
                        except Exception as e:
                            st.error(f"Erro na auto-indexação: {str(e)}")
            
            if uploaded_files:
                if st.button("🔄 Indexar Documentos"):
                    try:
                        from tools import vectorize_financial_reports
                        import tempfile
                        import os
                        
                        documents = []
                        processed_files = []
                        failed_files = []
                        
                        for uploaded_file in uploaded_files:
                            try:
                                # Criar arquivo temporário
                                with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
                                    tmp_file.write(uploaded_file.getvalue())
                                    tmp_path = tmp_file.name
                                
                                # Processar arquivo usando nossa função
                                from tools import read_file_content
                                content = read_file_content(tmp_path)
                                
                                # Verificar se foi processado com sucesso
                                if "❌ Erro" in content or "não suportado" in content:
                                    failed_files.append(f"{uploaded_file.name}: {content}")
                                else:
                                    documents.append(f"📄 {uploaded_file.name}:\n{content}")
                                    processed_files.append(uploaded_file.name)
                                
                                # Limpar arquivo temporário
                                os.unlink(tmp_path)
                                
                            except Exception as e:
                                failed_files.append(f"{uploaded_file.name}: Erro - {str(e)}")
                        
                        # Mostrar status de processamento
                        if processed_files:
                            st.info(f"📄 Arquivos processados: {', '.join(processed_files)}")
                        
                        if failed_files:
                            st.warning("⚠️ Arquivos com problema:")
                            for failure in failed_files:
                                st.text(f"  • {failure}")
                        
                        # Indexar documentos processados com sucesso
                        if documents:
                            with st.spinner(f"Indexando {len(documents)} documentos..."):
                                result = vectorize_financial_reports.invoke({"reports": documents})
                            
                            if result["status"] == "success":
                                st.success(f"✅ {result['documents_added']} documentos indexados com sucesso!")
                                st.info(f"📊 Total no banco: {result['total_documents']} documentos")
                            else:
                                st.error(f"❌ Erro na indexação: {result['message']}")
                        else:
                            st.error("❌ Nenhum documento foi processado com sucesso")
                            
                    except Exception as e:
                        st.error(f"❌ Erro geral: {str(e)}")
            
            # Indexar documentos de exemplo
            st.subheader("📊 Documentos de Exemplo")
            if st.button("📁 Carregar Exemplos"):
                try:
                    from tools import vectorize_financial_reports, SAMPLE_FINANCIAL_REPORTS
                    
                    with st.spinner("Carregando documentos de exemplo..."):
                        result = vectorize_financial_reports.invoke({"reports": SAMPLE_FINANCIAL_REPORTS})
                    
                    if result["status"] == "success":
                        st.success(f"✅ {len(SAMPLE_FINANCIAL_REPORTS)} documentos de exemplo carregados!")
                        st.info(f"Total: {result['total_documents']} documentos")
                    else:
                        st.error(f"❌ Erro: {result['message']}")
                        
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")
            
            st.divider()
            
            # Gerenciar banco de dados
            st.header("�️ Banco de Dados")
            
            try:
                from tools import get_vector_stats, clear_vector_database
                stats = get_vector_stats.invoke({})
                
                st.metric("Documentos Indexados", stats["total_documents"])
                st.metric("Coleção", stats["collection_name"])
                st.info(f"💾 Armazenamento: {stats['storage_path']}")
                
                # Botão para limpar banco
                if stats["total_documents"] > 0:
                    if st.button("🗑️ Limpar Banco", type="secondary"):
                        if st.session_state.get("confirm_clear", False):
                            with st.spinner("Limpando banco de dados..."):
                                result = clear_vector_database.invoke({})
                            if result["status"] == "success":
                                st.success(f"✅ {result['message']}")
                                st.rerun()
                            st.session_state["confirm_clear"] = False
                        else:
                            st.session_state["confirm_clear"] = True
                            st.warning("⚠️ Clique novamente para confirmar a limpeza")
                
                # Listar documentos indexados
                if stats["total_documents"] > 0:
                    with st.expander("📋 Ver Documentos Indexados"):
                        try:
                            import chromadb
                            from chromadb.config import Settings
                            
                            client = chromadb.PersistentClient(
                                path='./chromadb_storage',
                                settings=Settings(anonymized_telemetry=False, allow_reset=True)
                            )
                            collection = client.get_collection('financial_reports')
                            all_data = collection.get()
                            
                            for i, (doc_id, document) in enumerate(zip(all_data['ids'], all_data['documents']), 1):
                                # Extrair nome do arquivo
                                first_line = document.split('\n')[0]
                                if '📄' in first_line:
                                    filename = first_line.replace('📄', '').strip().rstrip(':')
                                else:
                                    filename = f"Documento {i}"
                                
                                # Mostrar preview
                                preview = document[:200] + "..." if len(document) > 200 else document
                                st.text_area(f"{i}. {filename}", preview, height=100, disabled=True, key=f"doc_{i}")
                                
                        except Exception as e:
                            st.error(f"Erro ao listar documentos: {e}")
                
            except Exception as e:
                st.warning(f"Status não disponível: {str(e)}")
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []

        conversational = st.columns((1, 14))
        output = st.empty()
        
        message_container = st.container()  
        
        # Container para input (será mostrado abaixo)
        input_container = st.container()
        
        # Área de input na parte inferior
        with input_container:
            conversational = st.columns((1, 14))
            if conversational[0].button(label="🗑️"):
                st.session_state["chat_history"] = []
                st.session_state["thread_id"] = str(uuid1())
                st.rerun()


        prompt = conversational[1].chat_input("Digite sua consulta:")
        
        if prompt:
            st.session_state["chat_history"].append({"role": "user", "content": prompt})
            
            config = {
                "configurable": {
                    "thread_id": st.session_state["thread_id"]
                }
            }

            try:
                response = run(prompt, config)
                # Estruturar resposta baseada no tipo de sistema usado
                assistant_response = {
                    "role": "assistant", 
                    "content": response["messages"][-1].content,
                    "docs": response.get("docs", None),
                    # Novos campos para RAG financeiro
                    "retrieved_doc": response.get("retrieved_doc", ""),
                    "similarity_score": response.get("similarity_score", 0.0),
                    "confidence": response.get("confidence", "")
                }
                
                st.session_state["chat_history"].append(assistant_response)
                
            except Exception as e:
                st.error(f"Erro durante a execução: {e}")
        
        # Exibe mensagens existentes no container com scroll
        with message_container:
            # Adiciona CSS para customizar a área de scroll
            st.markdown("""
                <style>
                    .stContainer {
                        max-height: 800px;
                        overflow-y: auto;
                        padding-right: 100px;
                    }
                </style>
            """, unsafe_allow_html=True)
            
            # Exibe as mensagens

            for msg in st.session_state["chat_history"]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    
                    # Sistema RAG financeiro - exibir informações detalhadas
                    if msg.get("retrieved_doc") and msg["role"] == "assistant":
                        with st.expander("📊 Informações do Sistema RAG Financeiro"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                confidence = msg.get("confidence", "")
                                similarity = msg.get("similarity_score", 0.0)
                                
                                if confidence == "alta":
                                    st.success(f"🟢 Confiança: **{confidence.upper()}**")
                                elif confidence == "média":
                                    st.warning(f"🟡 Confiança: **{confidence.upper()}**")
                                else:
                                    st.error(f"🔴 Confiança: **{confidence.upper()}**")
                                    
                            with col2:
                                st.metric("Similaridade", f"{similarity:.2%}")
                                
                            # Documento recuperado
                            st.subheader("📋 Documento Fonte")
                            with st.container():
                                st.text_area(
                                    "Relatório recuperado:", 
                                    msg["retrieved_doc"][:500] + "..." if len(msg["retrieved_doc"]) > 500 else msg["retrieved_doc"],
                                    height=150,
                                    disabled=True
                                )
                    
                    # Sistema tradicional - manter compatibilidade
                    elif msg.get("docs"):
                        for i, doc in enumerate(msg.get("docs")):
                            expander = st.expander(f"Referência {i+1}")  
                            expander.write(doc["page_content"])

    else:
        st.error("Erro")

build_page(is_on=True)