"""
Componentes de Usabilidade para o Desktop SerPleno
Inclui feedback visual, loading states, mensagens e atalhos de teclado.
"""
import customtkinter as ctk
from typing import Optional, Callable, Dict, Any, List
import threading
import time
from ui_theme import THEME, SPACING, RADIUS, font


class LoadingOverlay:
    """
    Overlay de carregamento para operações demoradas.
    
    Usage:
        overlay = LoadingOverlay(parent, "Carregando dados...")
        overlay.show()
        # ... operação ...
        overlay.hide()
    """
    
    def __init__(self, parent, message: str = "Carregando..."):
        self.parent = parent
        self.message = message
        self.overlay: Optional[ctk.CTkFrame] = None
        self.progress: Optional[ctk.CTkProgressBar] = None
    
    def show(self):
        """Mostra o overlay de carregamento."""
        if self.overlay:
            return
        
        # Criar overlay
        self.overlay = ctk.CTkFrame(
            self.parent,
            fg_color="#00000099",
            corner_radius=0
        )
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Container central
        container = ctk.CTkFrame(
            self.overlay,
            fg_color=THEME["card"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=THEME["border"]
        )
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Mensagem
        label = ctk.CTkLabel(
            container,
            text=self.message,
            font=font(14, "bold"),
            text_color=THEME["text"]
        )
        label.pack(padx=40, pady=(20, 10))
        
        # Barra de progresso indeterminada
        self.progress = ctk.CTkProgressBar(
            container,
            mode="indeterminate",
            width=200
        )
        self.progress.pack(padx=40, pady=(0, 20))
        self.progress.start()
        
        # Mudar cursor
        self.parent.configure(cursor="watch")
        self.parent.update()
    
    def hide(self):
        """Esconde o overlay de carregamento."""
        if self.overlay:
            if self.progress:
                self.progress.stop()
            self.overlay.destroy()
            self.overlay = None
            self.progress = None
        
        self.parent.configure(cursor="")
        self.parent.update()
    
    def update_message(self, message: str):
        """Atualiza a mensagem do overlay."""
        self.message = message
        if self.overlay:
            for child in self.overlay.winfo_children():
                for subchild in child.winfo_children():
                    if isinstance(subchild, ctk.CTkLabel):
                        subchild.configure(text=message)


class Toast:
    """
    Notificação toast temporária.
    
    Usage:
        Toast(parent, "Operação realizada com sucesso!", type="success")
        Toast(parent, "Erro ao processar", type="error")
    """
    
    def __init__(
        self, 
        parent, 
        message: str, 
        duration: int = 3000,
        toast_type: str = "info"
    ):
        self.parent = parent
        self.message = message
        self.duration = duration
        self.toast_type = toast_type
        
        # Cores por tipo
        self.colors = {
            "info": {"bg": THEME["primary"], "text": "white"},
            "success": {"bg": "#22C55E", "text": "white"},
            "warning": {"bg": "#F59E0B", "text": "white"},
            "error": {"bg": "#EF4444", "text": "white"}
        }
        
        self._show()
    
    def _show(self):
        """Mostra o toast."""
        colors = self.colors.get(self.toast_type, self.colors["info"])
        
        toast = ctk.CTkFrame(
            self.parent,
            fg_color=colors["bg"],
            corner_radius=8
        )
        toast.place(relx=0.5, rely=0.05, anchor="n")
        
        # Ícone baseado no tipo
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        
        icon_label = ctk.CTkLabel(
            toast,
            text=icons.get(self.toast_type, "ℹ️"),
            font=font(14),
            text_color=colors["text"]
        )
        icon_label.pack(side="left", padx=(12, 0), pady=12)
        
        label = ctk.CTkLabel(
            toast,
            text=self.message,
            font=font(12),
            text_color=colors["text"]
        )
        label.pack(side="left", padx=(8, 12), pady=12)
        
        # Remover após duração
        self.parent.after(self.duration, lambda: toast.destroy())


class ConfirmDialog:
    """
    Diálogo de confirmação.
    
    Usage:
        def on_confirm():
            print("Confirmado!")
        
        ConfirmDialog(
            parent,
            title="Confirmar Exclusão",
            message="Deseja realmente excluir?",
            on_confirm=on_confirm
        )
    """
    
    def __init__(
        self,
        parent,
        title: str = "Confirmação",
        message: str = "Deseja continuar?",
        confirm_text: str = "Confirmar",
        cancel_text: str = "Cancelar",
        danger: bool = False,
        on_confirm: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None
    ):
        self.parent = parent
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        
        # Criar modal
        self.modal = ctk.CTkToplevel(parent)
        self.modal.title(title)
        self.modal.geometry("400x180")
        self.modal.resizable(False, False)
        self.modal.transient(parent.winfo_toplevel())
        self.modal.grab_set()
        
        # Centralizar
        self.modal.update_idletasks()
        x = (self.modal.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.modal.winfo_screenheight() // 2) - (180 // 2)
        self.modal.geometry(f"+{x}+{y}")
        
        # Container
        container = ctk.CTkFrame(self.modal, fg_color=THEME["card"])
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(
            container,
            text=title,
            font=font(16, "bold"),
            text_color=THEME["text"]
        ).pack(pady=(0, 10))
        
        # Mensagem
        ctk.CTkLabel(
            container,
            text=message,
            font=font(12),
            text_color=THEME["text_muted"],
            wraplength=350
        ).pack(pady=(0, 20))
        
        # Botões
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack()
        
        # Botão cancelar
        ctk.CTkButton(
            btn_frame,
            text=cancel_text,
            width=100,
            fg_color=THEME["bg_alt"],
            text_color=THEME["text"],
            hover_color=THEME["border"],
            command=self._cancel
        ).pack(side="left", padx=8)
        
        # Botão confirmar
        confirm_color = "#EF4444" if danger else THEME["primary"]
        confirm_hover = "#DC2626" if danger else THEME["primary_hover"]
        
        ctk.CTkButton(
            btn_frame,
            text=confirm_text,
            width=100,
            fg_color=confirm_color,
            hover_color=confirm_hover,
            command=self._confirm
        ).pack(side="left", padx=8)
        
        # Bindings
        self.modal.bind("<Escape>", lambda e: self._cancel())
        self.modal.bind("<Return>", lambda e: self._confirm())
    
    def _confirm(self):
        """Confirma a ação."""
        self.modal.destroy()
        if self.on_confirm:
            self.on_confirm()
    
    def _cancel(self):
        """Cancela a ação."""
        self.modal.destroy()
        if self.on_cancel:
            self.on_cancel()


class KeyboardShortcuts:
    """
    Gerenciador de atalhos de teclado.
    
    Usage:
        shortcuts = KeyboardShortcuts(widget)
        shortcuts.bind("Ctrl+S", salvar)
        shortcuts.bind("Ctrl+N", novo)
        shortcuts.bind("Escape", fechar)
    """
    
    def __init__(self, widget):
        self.widget = widget
        self._shortcuts: Dict[str, Callable] = {}
        self._setup_bindings()
    
    def _setup_bindings(self):
        """Configura bindings de eventos."""
        # Mapear teclas modificadoras
        self._key_map = {
            "Ctrl": "Control",
            "Alt": "Alt",
            "Shift": "Shift",
            "Cmd": "Command"
        }
        
        # Bind para capturar todas as teclas
        self.widget.bind_all("<KeyPress>", self._handle_keypress)
    
    def bind(self, shortcut: str, callback: Callable):
        """
        Registra um atalho de teclado.
        
        Args:
            shortcut: Atalho no formato "Ctrl+S", "Escape", "F1", etc.
            callback: Função a ser chamada
        """
        # Normalizar atalho
        parts = shortcut.split("+")
        key = parts[-1].lower()
        modifiers = [p.strip() for p in parts[:-1]]
        
        # Construir sequência de binding
        sequence = "<"
        for mod in modifiers:
            mod_key = self._key_map.get(mod, mod)
            sequence += f"{mod_key}-"
        sequence += f"{key}>"
        
        self._shortcuts[sequence] = callback
        self.widget.bind_all(sequence, lambda e, cb=callback: cb())
    
    def unbind(self, shortcut: str):
        """Remove um atalho."""
        parts = shortcut.split("+")
        key = parts[-1].lower()
        modifiers = [p.strip() for p in parts[:-1]]
        
        sequence = "<"
        for mod in modifiers:
            mod_key = self._key_map.get(mod, mod)
            sequence += f"{mod_key}-"
        sequence += f"{key}>"
        
        if sequence in self._shortcuts:
            del self._shortcuts[sequence]
            self.widget.unbind_all(sequence)
    
    def _handle_keypress(self, event):
        """Processa evento de tecla pressionada."""
        # Este método pode ser usado para logging ou debug
        pass
    
    def get_shortcuts(self) -> Dict[str, str]:
        """Retorna lista de atalhos registrados."""
        return {k: v.__name__ if hasattr(v, '__name__') else str(v) 
                for k, v in self._shortcuts.items()}


class ErrorMessage:
    """
    Mensagem de erro detalhada.
    
    Usage:
        ErrorMessage(
            parent,
            title="Erro ao Carregar Dados",
            message="Não foi possível carregar a lista de estudantes.",
            details="Verifique sua conexão com o servidor.",
            suggestion="Tente novamente em alguns instantes."
        )
    """
    
    def __init__(
        self,
        parent,
        title: str = "Erro",
        message: str = "Ocorreu um erro.",
        details: Optional[str] = None,
        suggestion: Optional[str] = None,
        on_retry: Optional[Callable] = None
    ):
        self.parent = parent
        
        # Criar modal
        self.modal = ctk.CTkToplevel(parent)
        self.modal.title(title)
        self.modal.geometry("450x280")
        self.modal.resizable(False, False)
        self.modal.transient(parent.winfo_toplevel())
        self.modal.grab_set()
        
        # Centralizar
        self.modal.update_idletasks()
        x = (self.modal.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.modal.winfo_screenheight() // 2) - (280 // 2)
        self.modal.geometry(f"+{x}+{y}")
        
        # Container
        container = ctk.CTkFrame(self.modal, fg_color=THEME["card"])
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Ícone e título
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        
        icon_frame = ctk.CTkFrame(
            header,
            width=40,
            height=40,
            fg_color="#FEE2E2",
            corner_radius=20
        )
        icon_frame.pack(side="left", padx=(0, 12))
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(
            icon_frame,
            text="❌",
            font=font(16)
        ).place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(
            header,
            text=title,
            font=font(14, "bold"),
            text_color=THEME["text"]
        ).pack(side="left")
        
        # Mensagem principal
        ctk.CTkLabel(
            container,
            text=message,
            font=font(12),
            text_color=THEME["text"],
            wraplength=400,
            justify="left"
        ).pack(anchor="w", pady=(0, 10))
        
        # Detalhes
        if details:
            details_frame = ctk.CTkFrame(
                container,
                fg_color=THEME["bg_alt"],
                corner_radius=8
            )
            details_frame.pack(fill="x", pady=(0, 10))
            
            ctk.CTkLabel(
                details_frame,
                text=details,
                font=font(11),
                text_color=THEME["text_muted"],
                wraplength=380,
                justify="left"
            ).pack(padx=12, pady=8)
        
        # Sugestão
        if suggestion:
            ctk.CTkLabel(
                container,
                text=f"💡 {suggestion}",
                font=font(11),
                text_color="#F59E0B",
                wraplength=400,
                justify="left"
            ).pack(anchor="w", pady=(0, 15))
        
        # Botões
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack()
        
        if on_retry:
            ctk.CTkButton(
                btn_frame,
                text="Tentar Novamente",
                width=120,
                fg_color=THEME["primary"],
                command=lambda: [self.modal.destroy(), on_retry()]
            ).pack(side="left", padx=8)
        
        ctk.CTkButton(
            btn_frame,
            text="Fechar",
            width=100,
            fg_color=THEME["bg_alt"],
            text_color=THEME["text"],
            hover_color=THEME["border"],
            command=self.modal.destroy
        ).pack(side="left", padx=8)
        
        # Bindings
        self.modal.bind("<Escape>", lambda e: self.modal.destroy())


class ProgressTracker:
    """
    Rastreador de progresso para operações em etapas.
    
    Usage:
        tracker = ProgressTracker(parent, ["Conectando", "Baixando", "Processando", "Concluído"])
        tracker.start()
        tracker.next_step("Conectando ao servidor...")
        tracker.next_step("Baixando dados...")
        tracker.complete()
    """
    
    def __init__(self, parent, steps: List[str]):
        self.parent = parent
        self.steps = steps
        self.current_step = 0
        
        # Criar frame
        self.frame = ctk.CTkFrame(parent, fg_color=THEME["card"], corner_radius=RADIUS["card"])
        
        # Título
        self.title_label = ctk.CTkLabel(
            self.frame,
            text="Processando",
            font=font(14, "bold"),
            text_color=THEME["text"]
        )
        self.title_label.pack(pady=(15, 10))
        
        # Barra de progresso
        self.progress = ctk.CTkProgressBar(
            self.frame,
            width=300,
            mode="determinate"
        )
        self.progress.pack(pady=(0, 10))
        self.progress.set(0)
        
        # Label de status
        self.status_label = ctk.CTkLabel(
            self.frame,
            text="Iniciando...",
            font=font(11),
            text_color=THEME["text_muted"]
        )
        self.status_label.pack(pady=(0, 15))
        
        # Indicadores de etapa
        steps_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        steps_frame.pack(pady=(0, 15))
        
        self.step_indicators = []
        for i, step in enumerate(steps):
            indicator = ctk.CTkLabel(
                steps_frame,
                text=f"○ {step}",
                font=font(10),
                text_color=THEME["text_muted"]
            )
            indicator.pack(side="left", padx=8)
            self.step_indicators.append(indicator)
    
    def start(self):
        """Inicia o tracker."""
        self.current_step = 0
        self.progress.set(0)
        self._update_indicators()
    
    def next_step(self, message: Optional[str] = None):
        """Avança para a próxima etapa."""
        if self.current_step < len(self.steps):
            self.current_step += 1
            self._update_indicators()
            
            if message:
                self.status_label.configure(text=message)
            
            # Atualizar progresso
            progress_value = self.current_step / len(self.steps)
            self.progress.set(progress_value)
    
    def complete(self):
        """Marca como concluído."""
        self.current_step = len(self.steps)
        self.progress.set(1)
        self.title_label.configure(text="Concluído!")
        self.status_label.configure(text="Operação finalizada com sucesso")
        self._update_indicators()
    
    def error(self, message: str):
        """Marca como erro."""
        self.title_label.configure(text="Erro", text_color="#EF4444")
        self.status_label.configure(text=message)
    
    def _update_indicators(self):
        """Atualiza os indicadores de etapa."""
        for i, indicator in enumerate(self.step_indicators):
            if i < self.current_step:
                indicator.configure(
                    text=f"● {self.steps[i]}",
                    text_color="#22C55E"
                )
            elif i == self.current_step:
                indicator.configure(
                    text=f"◐ {self.steps[i]}",
                    text_color=THEME["primary"]
                )
            else:
                indicator.configure(
                    text=f"○ {self.steps[i]}",
                    text_color=THEME["text_muted"]
                )
    
    def pack(self, **kwargs):
        """Pack do frame."""
        self.frame.pack(**kwargs)
    
    def place(self, **kwargs):
        """Place do frame."""
        self.frame.place(**kwargs)
    
    def destroy(self):
        """Destrói o frame."""
        self.frame.destroy()


def show_loading(func):
    """
    Decorator para mostrar loading durante execução de função.
    
    Usage:
        @show_loading
        def minha_funcao(parent):
            # ... operação demorada ...
            pass
    """
    def wrapper(parent, *args, **kwargs):
        overlay = LoadingOverlay(parent, "Processando...")
        overlay.show()
        try:
            result = func(parent, *args, **kwargs)
            return result
        finally:
            overlay.hide()
    return wrapper


def run_with_loading(
    parent,
    func: Callable,
    on_complete: Optional[Callable] = None,
    on_error: Optional[Callable] = None,
    message: str = "Processando..."
):
    """
    Executa função com loading em thread separada.
    
    Usage:
        def minha_operacao():
            # ... operação demorada ...
            return resultado
        
        run_with_loading(
            parent,
            minha_operacao,
            on_complete=lambda r: print(f"Resultado: {r}"),
            message="Carregando dados..."
        )
    """
    overlay = LoadingOverlay(parent, message)
    overlay.show()
    
    def _run():
        try:
            result = func()
            if on_complete:
                parent.after(0, lambda: on_complete(result))
        except Exception as e:
            if on_error:
                parent.after(0, lambda: on_error(e))
        finally:
            parent.after(0, overlay.hide)
    
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
