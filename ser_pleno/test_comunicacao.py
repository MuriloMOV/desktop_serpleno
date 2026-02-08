#!/usr/bin/env python3
"""
Teste para o serviço de comunicação interna
"""
import sys
import traceback
import mysql.connector
from config.db_config import DB_CONFIG, get_db_connection
from services.comunicacao import ServicoComunicacao


def test_database_connection():
    """Testa a conexão com o banco de dados MySQL"""
    print("# Teste de Conexão com Banco de Dados #")
    print("=" * 50)
    
    try:
        # Conecta ao banco usando get_db_connection()
        print("Testando get_db_connection():", end=" ")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        print("OK")
        
        # Testa consulta básica
        print("Consultando database():", end=" ")
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()["DATABASE()"]
        print(db_name)
        
        # Testa consulta count no auth_user
        print("Contando usuários (auth_user):", end=" ")
        cursor.execute("SELECT COUNT(*) as count FROM auth_user")
        user_count = cursor.fetchone()["count"]
        print(user_count)
        
        # Testa consulta count no desktop_message
        print("Contando mensagens (desktop_message):", end=" ")
        cursor.execute("SELECT COUNT(*) as count FROM desktop_message")
        message_count = cursor.fetchone()["count"]
        print(message_count)
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERRO: {type(e).__name__}: {e}")
        return False


def test_servico_comunicacao():
    """Testa o serviço de comunicação"""
    print("\n# Teste do ServiçoComunicacao #")
    print("=" * 50)
    
    try:
        servico = ServicoComunicacao()
        
        # Listar contatos
        print("Listando contatos (listar_contatos):", end=" ")
        contatos = servico.listar_contatos()
        if not contatos["success"]:
            raise Exception("Erro ao listar contatos")
        print(f"{len(contatos['data'])} contatos encontrados")
        
        # Exibe detalhes de cada contato
        for i, c in enumerate(contatos['data'][:5]):
            print(f"Contato {i+1}: {c['name']} ({c['role']})")
            
        # Se houver contatos, tenta enviar mensagem
        if contatos['data']:
            print(f"\nEnviando mensagem para {contatos['data'][0]['name']}:", end=" ")
            resultado = servico.enviar_mensagem(
                1,  # ID do usuário logado (admin)
                contatos['data'][0]['id'],
                "Olá! Esta é uma mensagem de teste do serviço de comunicação."
            )
            
            if resultado['success']:
                print(f"OK (ID: {resultado['data']['id']})")
                
                # Obtém mensagens com o contato
                print(f"Obtendo mensagens com {contatos['data'][0]['name']}:", end=" ")
                mensagens = servico.obter_mensagens(1, contatos['data'][0]['id'])
                if mensagens['success']:
                    print(f"{len(mensagens['data'])} mensagens")
                    
                    for msg in mensagens['data']:
                        direcao = "Eu" if msg['sender_id'] == 1 else contatos['data'][0]['name']
                        print(f"  [{direcao}]: {msg['text']}")
                else:
                    raise Exception("Erro ao obter mensagens")
            else:
                raise Exception("Erro ao enviar mensagem")
                
        return True
                
    except Exception as e:
        print(f"ERRO: {type(e).__name__}: {e}")
        return False


def main():
    """Função principal"""
    print("Teste para o Sistema de Comunicação Interna")
    print("=" * 50)
    
    # Teste 1: Conexão com banco de dados
    if not test_database_connection():
        print("\n❌ Falha no teste de conexão com banco de dados")
        return 1
        
    # Teste 2: Serviço de comunicação
    if not test_servico_comunicacao():
        print("\n❌ Falha no teste do serviço de comunicação")
        return 2
        
    print("\n✅ Todos os testes passaram com sucesso!")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        print(traceback.format_exc())
        sys.exit(1)
