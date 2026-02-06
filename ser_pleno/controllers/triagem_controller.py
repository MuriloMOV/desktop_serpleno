class TriagemController:
    def __init__(self, view):
        self.view = view
        # Dados mestre agora ficam aqui no Controller
        self.data_master = [
            {"student": "Bruno Henrique", "date": "23/01/2026", "priority": "Alta", "status": "Pendente"},
            {"student": "Diego Martins", "date": "22/01/2026", "priority": "Média", "status": "Pendente"},
            {"student": "Carla Diaz", "date": "20/01/2026", "priority": "Baixa", "status": "Concluída"},
            {"student": "Ana Beatriz", "date": "19/01/2026", "priority": "Urgente", "status": "Pendente"},
            {"student": "Ana Laura", "date": "24/01/2026", "priority": "Baixa", "status": "Cancelada"},
        ]

    def carregar_dados_iniciais(self):
        """Chamado quando a View termina de carregar."""
        self.view.renderizar_tabela(self.data_master)

    def obter_metricas(self):
        """Calcula as métricas e devolve para a View."""
        return [
            {"label": "Total", "value": str(len(self.data_master)), "icon": "📋", "color": "#3B82F6"},
            {"label": "Pendentes", "value": "3", "icon": "⏳", "color": "#F59E0B"},
            {"label": "Concluídas", "value": "1", "icon": "✅", "color": "#10B981"},
            {"label": "Alta Prioridade", "value": "2", "icon": "⚠️", "color": "#EF4444"}
        ]

    def aplicar_filtros(self, status, prioridade):
        """Lógica de filtro que antes ficava na View."""
        filtered = []
        for d in self.data_master:
            match_status = (status == "Todos" or d["status"] == status)
            match_prioridade = (prioridade == "Todas" or d["priority"] == prioridade)
            if match_status and match_prioridade:
                filtered.append(d)
        
        self.view.renderizar_tabela(filtered)

    def limpar_filtros(self):
        """Reseta a tabela para o estado original."""
        self.view.renderizar_tabela(self.data_master)

    def get_priority_color(self, p):
        """Helper para cores de prioridade."""
        colors = {"Alta": "#EF4444", "Urgente": "#B91C1C", "Média": "#F59E0B", "Baixa": "#10B981"}
        return colors.get(p, "#10B981")

    # --- O MÉTODO QUE ESTAVA FALTANDO ---
    def abrir_nova_triagem(self):
        """Ação do botão + Nova Triagem."""
        print("Controller: Abrindo modal de nova triagem...")
        # Aqui no futuro você instanciará a sua Modal

    def visualizar_detalhes(self, item):
        """Ação do botão de olho (👁️)."""
        print(f"Controller: Visualizando detalhes de {item['student']}")