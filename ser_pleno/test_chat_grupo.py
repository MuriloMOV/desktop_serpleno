#!/usr/bin/env python3
"""
Teste para a funcionalidade de chat em grupo do Sistema de Comunicação Interna
"""

import sys
import traceback
from services.comunicacao import ServicoComunicacao


def test_chat_grupo():
    """Testa a funcionalidade de chat em grupo"""
    print("=== Teste de Chat em Grupo ===")
    print("=" * 50)
    
    try:
        servico = ServicoComunicacao()
        
        # Teste 1: Listar contatos com chat em grupo
        print("\n1. Verificando lista de contatos com chat em grupo:")
        contatos = servico.listar_contatos()
        if not contatos['success']:
            raise Exception("Erro ao listar contatos")
        
        print(f"   Quantidade de contatos: {len(contatos['data'])}")
        for i, c in enumerate(contatos['data']):
            print(f"   {i+1}. Nome: {c['name']} | Cargo: {c['role']} | ID: {c['id']}")
        
        # Teste 2: Enviar mensagem para chat em grupo
        print("\n2. Enviando mensagem para chat em grupo:")
        mensagem_teste = "Olá grupo! Esta é uma mensagem de teste para o chat em grupo."
        resultado_envio = servico.enviar_mensagem_grupo(5, mensagem_teste)
        
        if resultado_envio['success']:
            print(f"   Sucesso! Mensagem enviada (ID: {resultado_envio['data']['id']})")
        else:
            raise Exception("Erro ao enviar mensagem de grupo")
        
        # Teste 3: Obter mensagens do chat em grupo
        print("\n3. Obtendo mensagens do chat em grupo:")
        mensagens_grupo = servico.obter_mensagens_grupo()
        
        if mensagens_grupo['success']:
            print(f"   Quantidade de mensagens: {len(mensagens_grupo['data'])}")
            for i, msg in enumerate(mensagens_grupo['data']):
                direcao = "Eu" if msg['sender_id'] == 5 else f"Usuário {msg['sender_id']}"
                print(f"   {i+1}. [{direcao}] ({msg['timestamp']}): {msg['text']}")
        
        print("\nTeste de chat em grupo concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro: {type(e).__name__}: {e}")
        print(traceback.format_exc())
        return False


def main():
    """Função principal"""
    print("Teste da Funcionalidade de Chat em Grupo")
    print("=" * 50)
    
    if not test_chat_grupo():
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
