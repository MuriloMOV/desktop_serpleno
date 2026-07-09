from ser_pleno.application.services.dashboard import ServicoDashboard

svc = ServicoDashboard()

print('=== Teste de Notificações ===')

print('\n1. Notificações de Ajuda:')
ajuda_notifs = svc.obter_notificacoes_ajuda()
print(f'   Quantidade: {len(ajuda_notifs)}')
for i, notif in enumerate(ajuda_notifs, 1):
    print(f'   {i}. {notif["titulo"]}')
    print(f'      {notif["descricao"]}')
    print(f'      Data: {notif["data"]} - Lida: {notif["lida"]}')

print('\n2. Notificações de Alertas:')
alertas_notifs = svc.obter_notificacoes_alertas()
print(f'   Quantidade: {len(alertas_notifs)}')
for i, notif in enumerate(alertas_notifs, 1):
    print(f'   {i}. {notif["titulo"]}')
    print(f'      {notif["descricao"]}')
    print(f'      Data: {notif["data"]} - Lida: {notif["lida"]}')

print('\n3. Marcar Notificação como Lida:')
if alertas_notifs:
    first_alert = alertas_notifs[0]
    svc.marcar_notificacao_como_lida(first_alert["id"], "alerta")
    print(f'   Notificação "{first_alert["titulo"]}" marcada como lida')

    # Verificar se a notificação foi atualizada
    updated_alerts = svc.obter_notificacoes_alertas()
    for notif in updated_alerts:
        if notif["id"] == first_alert["id"]:
            print(f'   Status atualizado: Lida = {notif["lida"]}')

print('\n=== Teste Concluído ===')

