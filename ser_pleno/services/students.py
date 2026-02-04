from services import api

class StudentService:
    """Compat wrapper para testes que esperam uma API de estudantes."""
    def list_students(self, page=1):
        return api.get("students/", params={"page": page})

    def get_student(self, student_id):
        return api.get(f"students/{student_id}/")

    def obter_relatorio_estudante(self, student_id):
        """Compat method: tenta usar a implementação local (ServicoEstudante) e se não disponível, cair para a API."""
        try:
            from services.estudantes import ServicoEstudante
            return ServicoEstudante().obter_relatorio_estudante(student_id)
        except Exception:
            # Fallback para API (caso o desktop esteja integrado via cliente HTTP)
            try:
                return api.get(f"students/{student_id}/report/")
            except Exception:
                return {"success": False, "message": "Impossível obter relatório"}