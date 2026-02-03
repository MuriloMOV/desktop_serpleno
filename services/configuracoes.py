from .api import api

class ServicoConfiguracoes:
    def obter_configuracoes(self):
        # Retorna as configurações do usuário atual
        return api.get('settings/preferences/')

    def atualizar_configuracoes(self, dados):
        return api.post('settings/preferences/update/', json=dados)
