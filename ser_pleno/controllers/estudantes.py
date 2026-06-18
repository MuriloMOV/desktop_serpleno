# -*- coding: utf-8 -*-
"""Controller de Estudantes — mediação entre View e Services."""

from services.estudantes import ServicoEstudante


class EstudantesController:
    """Coordena as requisições da View de Estudantes."""

    def __init__(self, servico=None):
        self.servico = servico or ServicoEstudante()

    def listar(self, busca=None, possui_laudo=None, requer_atencao=None, pagina=1):
        return self.servico.listar_estudantes(
            busca=busca,
            possui_laudo=possui_laudo,
            requer_atencao=requer_atencao,
            pagina=pagina,
        )

    def obter(self, id_estudante):
        return self.servico.obter_estudante(id_estudante)

    def obter_relatorio(self, id_estudante):
        return self.servico.obter_relatorio_estudante(id_estudante)

    def criar(self, dados):
        return self.servico.criar_estudante(dados)

    def atualizar(self, id_estudante, dados):
        return self.servico.atualizar_estudante(id_estudante, dados)

    def deletar(self, id_estudante):
        return self.servico.deletar_estudante(id_estudante)
