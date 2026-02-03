from .api import api

class ServicoBemEstar:
    def obter_dashboard(self):
        return api.get("wellness/dashboard/")

    def listar_entradas_humor(self):
        return api.get("wellness/mood/")

    def obter_medias_humor(self):
        return api.get("wellness/mood/averages/")

    def obter_humor_estudante(self, id_estudante):
        return api.get(f"wellness/mood/student/{id_estudante}/")

    def listar_checkins(self):
        return api.get("wellness/checkins/")

    def listar_estudantes_risco(self):
        """Retorna estudantes em zona de risco emocional/comportamental"""
        return api.get("wellness/risk-students/")
