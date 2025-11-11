#!/usr/bin/env python3
"""
🗑️ Limpador de Banco de Dados ChromaDB
=====================================

Script para limpar ou resetar o banco de dados vetorial.
"""

import os
import sys
from pathlib import Path

def main():
    print("🗑️ Limpador do Banco de Dados RAG")
    print("=" * 40)
    
    try:
        from tools import clear_vector_database, reset_vector_database, get_vector_stats
    except ImportError as e:
        print(f"❌ Erro ao importar ferramentas: {e}")
        return
    
    # Mostrar status atual
    print("\n📊 Status atual do banco:")
    try:
        stats = get_vector_stats.invoke({})
        print(f"   📄 Total de documentos: {stats['total_documents']}")
        print(f"   📁 Caminho: {stats['storage_path']}")
        print(f"   🏷️ Coleção: {stats['collection_name']}")
        print(f"   🟢 Status: {stats.get('status', 'unknown')}")
    except Exception as e:
        print(f"   ❌ Erro ao verificar status: {e}")
        return
    
    if stats['total_documents'] == 0:
        print("\n✅ Banco já está vazio!")
        return
    
    # Opções de limpeza
    print(f"\n🔧 Opções de limpeza:")
    print(f"   1 - Limpar documentos (manter estrutura)")
    print(f"   2 - Reset completo (recriar banco)")
    print(f"   3 - Deletar arquivos físicos do disco")
    print(f"   4 - Cancelar")
    
    choice = input(f"\n🔢 Escolha uma opção (1-4): ").strip()
    
    if choice == "1":
        print(f"\n🧹 Limpando documentos...")
        try:
            result = clear_vector_database.invoke({})
            if result['status'] == 'success':
                print(f"   ✅ {result['message']}")
            else:
                print(f"   ⚠️ {result['message']}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            
    elif choice == "2":
        print(f"\n🔄 Resetando banco completamente...")
        try:
            result = reset_vector_database.invoke({})
            if result['status'] == 'success':
                print(f"   ✅ {result['message']}")
            else:
                print(f"   ⚠️ {result['message']}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            
    elif choice == "3":
        db_path = Path("./chromadb_storage")
        if db_path.exists():
            confirm = input(f"\n⚠️ Deletar pasta {db_path} completamente? (s/N): ").strip().lower()
            if confirm in ['s', 'sim', 'y', 'yes']:
                try:
                    import shutil
                    shutil.rmtree(db_path)
                    print(f"   ✅ Pasta {db_path} deletada com sucesso!")
                except Exception as e:
                    print(f"   ❌ Erro ao deletar: {e}")
            else:
                print(f"   ⏹️ Operação cancelada")
        else:
            print(f"   ℹ️ Pasta {db_path} não existe")
            
    elif choice == "4":
        print(f"\n⏹️ Operação cancelada")
        
    else:
        print(f"\n❌ Opção inválida: {choice}")
        return
    
    # Verificar status final
    if choice in ["1", "2"]:
        print(f"\n📊 Status após limpeza:")
        try:
            new_stats = get_vector_stats.invoke({})
            print(f"   📄 Total de documentos: {new_stats['total_documents']}")
            print(f"   🟢 Status: {new_stats.get('status', 'unknown')}")
        except Exception as e:
            print(f"   ❌ Erro ao verificar novo status: {e}")

if __name__ == "__main__":
    main()