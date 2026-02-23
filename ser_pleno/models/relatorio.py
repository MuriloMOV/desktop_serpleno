import customtkinter as ctk
from ui_theme import THEME, RADIUS, font

class NovoRelatorioModal(ctk.CTkToplevel):
    def __init__(self, parent, tipos, callback):
        super().__init__(parent)
        self.title("Gerar Novo Relatório")
        self.geometry("400x500")
        self.callback = callback
        self.tipos_dict = dict(tipos) # Para converter 'Relatório Geral' -> 'general'

        # Configuração de Janela (Ficar na frente)
        self.lift()
        self.grab_set()
        
        self.configure(fg_color=THEME["card"])
        self._criar_layout(list(self.tipos_dict.values()))

    def _criar_layout(self, lista_nomes_tipos):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)

        ctk.CTkLabel(container, text="Novo Relatório", font=font(18, "bold")).pack(anchor="w", pady=(0, 20))

        # Campo Nome (name no Django)
        ctk.CTkLabel(container, text="Nome do Relatório", font=font(12)).pack(anchor="w", pady=(10, 5))
        self.entry_nome = ctk.CTkEntry(container, placeholder_text="Ex: Mensal Fevereiro", height=40)
        self.entry_nome.pack(fill="x")

        # Campo Tipo (report_type no Django)
        ctk.CTkLabel(container, text="Tipo de Relatório", font=font(12)).pack(anchor="w", pady=(10, 5))
        self.combo_tipo = ctk.CTkOptionMenu(container, values=lista_nomes_tipos, height=40, fg_color=THEME["bg_alt"], text_color=THEME["text"])
        self.combo_tipo.pack(fill="x")

        # Campo Formato (format no Django)
        ctk.CTkLabel(container, text="Formato de Saída", font=font(12)).pack(anchor="w", pady=(10, 5))
        self.combo_format = ctk.CTkOptionMenu(container, values=["PDF", "Excel", "CSV"], height=40, fg_color=THEME["bg_alt"], text_color=THEME["text"])
        self.combo_format.pack(fill="x")

        # Botões
        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x", pady=(30, 0))

        ctk.CTkButton(btn_box, text="Cancelar", fg_color="transparent", border_width=1, 
                      text_color=THEME["text"], command=self.destroy).pack(side="left", padx=(0, 10), expand=True, fill="x")
        
        ctk.CTkButton(btn_box, text="Gerar e Salvar", fg_color=THEME["primary"], 
                      command=self._confirmar).pack(side="right", expand=True, fill="x")

    def _confirmar(self):
        # Mapeia de volta para os valores que o Django entende
        nome_tipo = self.combo_tipo.get()
        valor_tipo = [k for k, v in self.tipos_dict.items() if v == nome_tipo][0]
        
        dados = {
            "name": self.entry_nome.get(),
            "report_type": valor_tipo,
            "format": self.combo_format.get().lower(),
        }
        
        self.callback(dados)
        self.destroy()