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
        """Lista contatos com conversas"""
        try:
            response = api.get('messages/contacts/')
            if response and response.get('success'):
                return response
            return {'success': False, 'results': []}
        except Exception as e:
            print(f"Erro ao listar contatos: {e}")
            return {'success': False, 'results': []}

    def obter_mensagens(self, id_usuario):
        """Obtém mensagens da conversa com um usuário"""
        try:
            response = api.get(f'messages/{id_usuario}/')
            if response and response.get('success'):
                return response
            return {'success': False, 'results': []}
        except Exception as e:
            print(f"Erro ao obter mensagens: {e}")
            return {'success': False, 'results': []}

    def enviar_mensagem(self, id_usuario, conteudo):
        """Envia mensagem para um usuário"""
        try:
            response = api.post('messages/send/', json={'recipient_id': id_usuario, 'text': conteudo})
            if response and response.get('success'):
                return response
            return {'success': False, 'message': response.get('message', 'Erro ao enviar mensagem')}
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
            return {'success': False, 'message': str(e)}

    def marcar_mensagem_lida(self, id_mensagem):
        """Marca mensagem como lida"""
        try:
            response = api.post(f'messages/{id_mensagem}/read/')
            return response
        except Exception as e:
            print(f"Erro ao marcar mensagem como lida: {e}")
            return {'success': False}

    def deletar_mensagem(self, id_mensagem):
        """Deleta mensagem"""
        try:
            response = api.delete(f'messages/{id_mensagem}/delete/')
            return response
        except Exception as e:
            print(f"Erro ao deletar mensagem: {e}")
            return {'success': False}
