from .api import api

class ServicoComunicacao:
    def listar_alertas(self):
        return api.get('alerts/')

    def marcar_alerta_lido(self, id_alerta):
        return api.post(f'alerts/{id_alerta}/read/')

    def marcar_todos_lidos(self):
        return api.post('alerts/read-all/')
        
    def listar_pedidos_ajuda(self):
        return api.get('help-requests/')

    def listar_contatos(self):
        return api.get('messages/contacts/')

    def obter_mensagens(self, id_usuario):
        return api.get(f'messages/{id_usuario}/')

    def enviar_mensagem(self, id_usuario, conteudo):
        return api.post('messages/send/', json={'recipient_id': id_usuario, 'content': conteudo})

    def marcar_mensagem_lida(self, id_mensagem):
        return api.post(f'messages/{id_mensagem}/read/')

    def deletar_mensagem(self, id_mensagem):
        return api.delete(f'messages/{id_mensagem}/delete/')
