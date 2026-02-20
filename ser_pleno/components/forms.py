"""
Componentes de Formulário reutilizáveis para CustomTkinter
"""
import customtkinter as ctk
from typing import Optional, Callable, Any, Dict
from ui_theme import THEME, RADIUS, font


class FormField(ctk.CTkFrame):
    """
    Campo de formulário com label e entry.
    
    Usage:
        field = FormField(parent, label="Nome", placeholder="Digite seu nome...")
        value = field.get()
    """
    
    def __init__(
        self,
        parent,
        label: str,
        placeholder: str = "",
        value: str = "",
        height: int = 36,
        width: Optional[int] = None,
        required: bool = False,
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self._label = label
        self._placeholder = placeholder
        self._required = required
        self._entry: Optional[ctk.CTkEntry] = None
        
        self._build_ui(height, width, value)
    
    def _build_ui(self, height: int, width: Optional[int], value: str):
        # Label
        label_text = f"{self._label} *" if self._required else self._label
        ctk.CTkLabel(
            self,
            text=label_text,
            font=font(11, "bold"),
            text_color=THEME["text"]
        ).pack(anchor="w")
        
        # Entry frame
        entry_frame = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["input"],
            border_width=1,
            border_color=THEME["border"],
            height=height
        )
        entry_frame.pack(fill="x", pady=(4, 0))
        entry_frame.pack_propagate(False)
        
        # Entry
        self._entry = ctk.CTkEntry(
            entry_frame,
            placeholder_text=self._placeholder,
            height=height - 6,
            border_width=0,
            fg_color="transparent",
            text_color=THEME["text"],
            font=font(12)
        )
        if width:
            self._entry.configure(width=width)
        self._entry.pack(side="left", fill="both", expand=True, padx=12)
        
        if value:
            self._entry.insert(0, value)
    
    def get(self) -> str:
        """Retorna o valor do campo"""
        return self._entry.get() if self._entry else ""
    
    def set(self, value: str):
        """Define o valor do campo"""
        if self._entry:
            self._entry.delete(0, "end")
            self._entry.insert(0, value)
    
    def clear(self):
        """Limpa o campo"""
        if self._entry:
            self._entry.delete(0, "end")
    
    def is_empty(self) -> bool:
        """Verifica se o campo está vazio"""
        return not self.get().strip()


class PasswordField(FormField):
    """Campo de senha com toggle de visibilidade"""
    
    def __init__(
        self,
        parent,
        label: str = "Senha",
        placeholder: str = "Digite sua senha...",
        **kwargs
    ):
        super().__init__(parent, label, placeholder, **kwargs)
        self._is_visible = False
    
    def _build_ui(self, height: int, width: Optional[int], value: str):
        # Label
        label_text = f"{self._label} *" if self._required else self._label
        ctk.CTkLabel(
            self,
            text=label_text,
            font=font(11, "bold"),
            text_color=THEME["text"]
        ).pack(anchor="w")
        
        # Entry frame
        entry_frame = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["input"],
            border_width=1,
            border_color=THEME["border"],
            height=height
        )
        entry_frame.pack(fill="x", pady=(4, 0))
        entry_frame.pack_propagate(False)
        
        # Ícone de cadeado
        ctk.CTkLabel(
            entry_frame,
            text="🔒",
            font=font(14),
            text_color=THEME["text_muted"]
        ).pack(side="left", padx=12)
        
        # Entry
        self._entry = ctk.CTkEntry(
            entry_frame,
            placeholder_text=self._placeholder,
            height=height - 6,
            border_width=0,
            fg_color="transparent",
            text_color=THEME["text"],
            show="•",
            font=font(12)
        )
        if width:
            self._entry.configure(width=width)
        self._entry.pack(side="left", fill="both", expand=True, padx=(0, 12))
        
        # Botão toggle
        self._toggle_btn = ctk.CTkLabel(
            entry_frame,
            text="👁",
            font=font(14),
            text_color=THEME["text_muted"],
            cursor="hand2"
        )
        self._toggle_btn.pack(side="right", padx=12)
        self._toggle_btn.bind("<Button-1>", self._toggle_visibility)
    
    def _toggle_visibility(self, event=None):
        self._is_visible = not self._is_visible
        self._entry.configure(show="" if self._is_visible else "•")
        self._toggle_btn.configure(text="👁‍🗨" if self._is_visible else "👁")


class TextAreaField(ctk.CTkFrame):
    """
    Campo de texto multilinha.
    
    Usage:
        field = TextAreaField(parent, label="Descrição", placeholder="Digite...", height=100)
        value = field.get()
    """
    
    def __init__(
        self,
        parent,
        label: str,
        placeholder: str = "",
        height: int = 80,
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self._label = label
        self._textbox: Optional[ctk.CTkTextbox] = None
        
        self._build_ui(height)
    
    def _build_ui(self, height: int):
        # Label
        ctk.CTkLabel(
            self,
            text=self._label,
            font=font(11, "bold"),
            text_color=THEME["text"]
        ).pack(anchor="w")
        
        # Textbox
        self._textbox = ctk.CTkTextbox(
            self,
            fg_color=THEME["bg_alt"],
            border_width=1,
            border_color=THEME["border"],
            height=height,
            corner_radius=RADIUS["input"],
            font=font(12)
        )
        self._textbox.pack(fill="x", pady=(4, 0))
    
    def get(self) -> str:
        """Retorna o valor do campo"""
        return self._textbox.get("0.0", "end-1c") if self._textbox else ""
    
    def set(self, value: str):
        """Define o valor do campo"""
        if self._textbox:
            self._textbox.delete("0.0", "end")
            self._textbox.insert("0.0", value)
    
    def clear(self):
        """Limpa o campo"""
        if self._textbox:
            self._textbox.delete("0.0", "end")


class SearchField(ctk.CTkFrame):
    """
    Campo de busca com ícone.
    
    Usage:
        search = SearchField(parent, placeholder="Buscar...", on_search=callback)
    """
    
    def __init__(
        self,
        parent,
        placeholder: str = "Buscar...",
        on_search: Optional[Callable[[str], None]] = None,
        on_clear: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self._on_search = on_search
        self._on_clear = on_clear
        self._entry: Optional[ctk.CTkEntry] = None
        
        self._build_ui(placeholder)
    
    def _build_ui(self, placeholder: str):
        frame = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["input"],
            border_width=1,
            border_color=THEME["border"],
            height=36
        )
        frame.pack(fill="x")
        frame.pack_propagate(False)
        
        # Ícone de lupa
        ctk.CTkLabel(
            frame,
            text="🔍",
            text_color=THEME["text_muted"],
            font=font(11)
        ).pack(side="left", padx=8)
        
        # Entry
        self._entry = ctk.CTkEntry(
            frame,
            placeholder_text=placeholder,
            fg_color="transparent",
            border_width=0,
            font=font(11)
        )
        self._entry.pack(side="left", fill="both", expand=True)
        
        # Bind events
        if self._on_search:
            self._entry.bind("<Return>", lambda e: self._on_search(self.get()))
            self._entry.bind("<KeyRelease>", lambda e: self._on_search(self.get()))
    
    def get(self) -> str:
        return self._entry.get() if self._entry else ""
    
    def clear(self):
        if self._entry:
            self._entry.delete(0, "end")
        if self._on_clear:
            self._on_clear()


class SelectField(ctk.CTkFrame):
    """
    Campo de seleção (dropdown).
    
    Usage:
        select = SelectField(parent, label="Status", options=["Ativo", "Inativo", "Pendente"])
        value = select.get()
    """
    
    def __init__(
        self,
        parent,
        label: str,
        options: list,
        default: str = None,
        on_change: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self._label = label
        self._options = options
        self._on_change = on_change
        self._menu: Optional[ctk.CTkOptionMenu] = None
        
        self._build_ui(default)
    
    def _build_ui(self, default: Optional[str]):
        # Label
        ctk.CTkLabel(
            self,
            text=self._label,
            font=font(11, "bold"),
            text_color=THEME["text"]
        ).pack(anchor="w")
        
        # OptionMenu
        default_value = default or (self._options[0] if self._options else "")
        self._menu = ctk.CTkOptionMenu(
            self,
            values=self._options,
            fg_color=THEME["card"],
            button_color=THEME["card"],
            button_hover_color=THEME["bg_alt"],
            font=font(12),
            height=36,
            corner_radius=RADIUS["input"],
            command=self._handle_change
        )
        self._menu.set(default_value)
        self._menu.pack(fill="x", pady=(4, 0))
    
    def _handle_change(self, value: str):
        if self._on_change:
            self._on_change(value)
    
    def get(self) -> str:
        return self._menu.get() if self._menu else ""
    
    def set(self, value: str):
        if self._menu:
            self._menu.set(value)


class CheckboxField(ctk.CTkFrame):
    """
    Campo de checkbox.
    
    Usage:
        checkbox = CheckboxField(parent, label="Aceito os termos", checked=False)
        is_checked = checkbox.get()
    """
    
    def __init__(
        self,
        parent,
        label: str,
        checked: bool = False,
        on_change: Optional[Callable[[bool], None]] = None,
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self._checkbox = ctk.CTkCheckBox(
            self,
            text=label,
            font=font(11),
            border_color=THEME["border"],
            checkmark_color=THEME["primary"],
            command=lambda: on_change(self.get()) if on_change else None
        )
        self._checkbox.pack(anchor="w")
        
        if checked:
            self._checkbox.select()
    
    def get(self) -> bool:
        return bool(self._checkbox.get())
    
    def set(self, checked: bool):
        if checked:
            self._checkbox.select()
        else:
            self._checkbox.deselect()


class Form(ctk.CTkFrame):
    """
    Container de formulário com múltiplos campos.
    
    Usage:
        form = Form(parent)
        form.add_field("nome", FormField(form, label="Nome"))
        form.add_field("email", FormField(form, label="Email"))
        data = form.get_data()
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._fields: Dict[str, Any] = {}
    
    def add_field(self, name: str, field: Any):
        """Adiciona um campo ao formulário"""
        self._fields[name] = field
        field.pack(fill="x", pady=8)
        return field
    
    def get_data(self) -> Dict[str, Any]:
        """Retorna todos os valores do formulário"""
        data = {}
        for name, field in self._fields.items():
            if hasattr(field, 'get'):
                data[name] = field.get()
        return data
    
    def set_data(self, data: Dict[str, Any]):
        """Define valores do formulário"""
        for name, value in data.items():
            if name in self._fields and hasattr(self._fields[name], 'set'):
                self._fields[name].set(value)
    
    def clear(self):
        """Limpa todos os campos"""
        for field in self._fields.values():
            if hasattr(field, 'clear'):
                field.clear()
    
    def validate(self) -> Dict[str, str]:
        """
        Valida campos obrigatórios.
        Retorna dict com erros (vazio se válido).
        """
        errors = {}
        for name, field in self._fields.items():
            if hasattr(field, '_required') and field._required:
                if hasattr(field, 'is_empty') and field.is_empty():
                    errors[name] = f"{field._label} é obrigatório"
        return errors
