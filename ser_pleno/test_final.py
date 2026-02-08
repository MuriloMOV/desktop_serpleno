from services.comunicacao import ServicoComunicacao

print("=== Teste Final - Comunicação Interna ===")
servico = ServicoComunicacao()

try:
    print("1. Carregando contatos com permissões admin/staff...")
    contatos = servico.listar_contatos()
    print(f"   Status: {'Sucesso' if contatos['success'] else 'Falha'}")
    if contatos['success']:
        print(f"   Quantidade de contatos: {len(contatos['data'])}")
        print("   Primeiros 5 contatos:")
        for i, c in enumerate(contatos['data'][:5]):
            print(f"   {i+1}. Nome: {c['name']} | Cargo: {c['role']} | ID: {c['id']}")
except Exception as e:
    print(f"Erro: {e}")

print("\n2. Verificando envio de mensagem...")
try:
    if contatos['success'] and len(contatos['data']) > 0:
        contato = contatos['data'][1]  # Analista com ID 6
        print(f"   Enviando mensagem para: {contato['name']} ({contato['id']})")
        resultado = servico.enviar_mensagem(
            5,  # ID do usuário logado (suporte)
            contato['id'], 
            'Teste de mensagem final'
        )
        print(f"   Status: {'Sucesso' if resultado['success'] else 'Falha'}")
        if resultado['success']:
            print(f"   ID da mensagem: {resultado['data']['id']}")
except Exception as e:
    print(f"Erro: {e}")

print("\n3. Verificando recebimento de mensagem...")
try:
    if contatos['success'] and len(contatos['data']) > 0:
        contato = contatos['data'][1]
        mensagens = servico.obter_mensagens(5, contato['id'])
        print(f"   Status: {'Sucesso' if mensagens['success'] else 'Falha'}")
        if mensagens['success']:
            print(f"   Quantidade de mensagens: {len(mensagens['data'])}")
            if len(mensagens['data']) > 0:
                print("   Última mensagem:")
                ultima = mensagens['data'][-1]
                print(f"   {ultima['text']}")
except Exception as e:
    print(f"Erro: {e}")
