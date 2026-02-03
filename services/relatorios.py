from .api import api

class ServicoRelatorio:
    def listar_relatorios(self, tipo=None, data_inicio=None, pagina=1):
        params = {'page': pagina}
        if tipo: params['type'] = tipo
        if data_inicio: params['date_from'] = data_inicio
        
        return api.get('reports/', params=params)

    def obter_estatisticas(self, periodo='month'):
        return api.get('reports/stats/', params={'period': periodo})

    def gerar_relatorio(self, dados):
        return api.post('reports/generate/', json=dados)

    def baixar_relatorio(self, id_relatorio):
        return api.get(f'reports/{id_relatorio}/download/')

    def deletar_relatorio(self, id_relatorio):
        return api.delete(f'reports/{id_relatorio}/delete/')

    def exportar_estudantes(self):
        return api.get('export/students/')

    def exportar_agendamentos(self):
        return api.get('export/appointments/')

    def exportar_triagens(self):
        return api.get('export/screenings/')
