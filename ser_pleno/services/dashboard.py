from repositories.dashboard import DashboardRepository

try:
    from services.api import api
except Exception:
    api = None


class ServicoDashboard:
    def __init__(self):
        self.repo = DashboardRepository()

    def obter_notificacoes_ajuda(self):
        """Obtém notificações de ajuda do serpleno_web."""
        try:
            from services.api import api

            response = api.get("help/notifications/")
            if response.get("success"):
                return response.get("data", [])
        except Exception as e:
            print(f"Erro ao obter notificações de ajuda: {e}")
        return [
            {
                "id": 1,
                "titulo": "Ajuda com agendamento",
                "descricao": "Você tem 5 agendamentos pendentes de confirmação",
                "data": "2026-02-11",
                "lida": False,
            },
            {
                "id": 2,
                "titulo": "Orientação sobre relatórios",
                "descricao": "Novo template de relatório disponível",
                "data": "2026-02-10",
                "lida": True,
            },
        ]

    def obter_notificacoes_alertas(self):
        """Obtém notificações de alertas do sistema."""
        from config.db_config import get_db_connection

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, alert_type, message, created_at, is_read FROM desktop_alert WHERE is_read = 0 ORDER BY created_at DESC"
        )
        alertas = cursor.fetchall()
        connection.close()

        return [
            {
                "id": alerta["id"],
                "titulo": self.formatar_tipo_alerta(alerta["alert_type"]) or "Alerta",
                "descricao": alerta["message"] or "Mensagem de alerta",
                "data": alerta["created_at"].strftime("%Y-%m-%d")
                if hasattr(alerta["created_at"], "strftime")
                else str(alerta["created_at"]),
                "lida": alerta["is_read"],
            }
            for alerta in alertas
        ]

    def formatar_tipo_alerta(self, alert_type):
        """Formata o tipo de alerta para exibição."""
        tipos = {
            "screening_pending": "Triagem Pendente",
            "appointment_reminder": "Lembrete de Consulta",
            "followup_required": "Acompanhamento Necessário",
            "high_risk": "Alto Risco",
            "missed_appointment": "Falta em Consulta",
            "system": "Alerta do Sistema",
        }
        return tipos.get(alert_type, alert_type.replace("_", " ").title())

    def marcar_notificacao_como_lida(self, notificacao_id, tipo="alerta"):
        """Marca uma notificação como lida."""
        if tipo == "alerta":
            from config.db_config import get_db_connection

            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE desktop_alert SET is_read = 1 WHERE id = %s", (notificacao_id,)
            )
            connection.commit()
            connection.close()
        elif tipo == "ajuda":
            try:
                from services.api import api

                api.put(f"help/notifications/{notificacao_id}/read/")
            except Exception as e:
                print(f"Erro ao marcar notificação de ajuda como lida: {e}")

    def obter_kpis(self):
        """Obtém estatísticas consolidadas do dashboard via repositório."""
        return self.repo.obter_kpis()
