from .api import api

class ServicoEstudante:
    def listar_estudantes(self, busca=None, possui_laudo=None, requer_atencao=None, pagina=1):
        params = {'page': pagina}
        if busca:
            params['search'] = busca
        if possui_laudo is not None:
            params['has_medical_report'] = str(possui_laudo).lower()
        if requer_atencao is not None:
            params['requires_attention'] = str(requer_atencao).lower()

        return api.get('students/', params=params)

    def obter_estudante(self, id_estudante):
        return api.get(f'students/{id_estudante}/')

    def criar_estudante(self, dados):
        return api.post('students/add/', json=dados)

    def atualizar_estudante(self, id_estudante, dados):
        return api.put(f'students/{id_estudante}/update/', json=dados)

    def deletar_estudante(self, id_estudante):
        return api.delete(f'students/{id_estudante}/delete/')
