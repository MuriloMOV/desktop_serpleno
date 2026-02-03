from .api import api

class ServicoMural:
    def listar_mensagens(self, busca=None, pagina=1):
        params = {'page': pagina}
        if busca: params['search'] = busca
        
        return api.get('board/messages/', params=params)

    def criar_mensagem(self, dados):
        return api.post('board/messages/add/', json=dados)
