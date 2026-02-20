"""
Componentes de Cards reutilizáveis para CustomTkinter
"""
import customtkinter as ctk
from typing import Optional, Callable, Dict, Any
from ui_theme import THEME, SPACING, RADIUS, font


class KPICard(ctk.CTkFrame):
    """
    Card de KPI para exibir métricas.
    
    Usage:
        card = KPICard(parent, title="Atendimentos", value="42", icon="👥", color="#6366F1")
    """
    
    def __init__(
        self,
        parent,
        title: str,
        value: str,
        icon: str = "📊",
        color: str = THEME["primary"],
        **kwargs
    ):
        super().__init__(
            parent,
            fg_color=THEME["card"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=THEME["border"],
            **kwargs
        )
        
        self._title = title
        self._value = value
        self._icon = icon
        self._color = color
        
        self._build_ui()
    
    def _build_ui(self):
        # Container de texto
        txt_frame = ctk.CTkFrame(self, fg_color="transparent")
        txt_frame.pack(side="left", padx=25, pady=25)
        
        # Título
        ctk.CTkLabel(
            txt_frame,
            text=self._title,
            font=font(13),
            text_color=THEME["text_muted"]
        ).pack(anchor="w")
        
        # Valor
        self._value_label = ctk.CTkLabel(
            txt_frame,
            text=self._value,
            font=font(28, "bold"),
            text_color=THEME["text"]
        )
        self._value_label.pack(anchor="w", pady=(5, 0))
        
        # Ícone
        bg_hex = self._blend_color(self._color, 0.1)
        ctk.CTkLabel(
            self,
            text=self._icon,
            font=font(22),
            text_color=self._color,
            fg_color=bg_hex,
            width=50,
            height=50,
            corner_radius=10
        ).pack(side="right", padx=25)
    
    def update_value(self, new_value: str):
        """Atualiza o valor exibido"""
        self._value_label.configure(text=new_value)
    
    @staticmethod
    def _blend_color(hex_c: str, alpha: float) -> str:
        """Mistura cor com branco"""
        r, g, b = int(hex_c[1:3], 16), int(hex_c[3:5], 16), int(hex_c[5:7], 16)
        return f"#{int(r*alpha + 255*(1-alpha)):02x}{int(g*alpha + 255*(1-alpha)):02x}{int(b*alpha + 255*(1-alpha)):02x}"


class ContainerCard(ctk.CTkFrame):
    """
    Card container com título e opcionalmente um link de ação.
    
    Usage:
        card = ContainerCard(parent, title="Próximos Atendimentos", link_text="Ver todos →")
        card.add_content(my_widget)
    """
    
    def __init__(
        self,
        parent,
        title: str,
        link_text: Optional[str] = None,
        link_callback: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(
            parent,
            fg_color=THEME["card"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=THEME["border"],
            **kwargs
        )
        
        self._title = title
        self._link_text = link_text
        self._link_callback = link_callback
        self._content_frame = None
        
        self._build_ui()
    
    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=20)
        
        # Título
        ctk.CTkLabel(
            header,
            text=self._title,
            font=font(16, "bold"),
            text_color=THEME["text"]
        ).pack(side="left")
        
        # Link de ação
        if self._link_text:
            link = ctk.CTkLabel(
                header,
                text=self._link_text,
                font=font(12),
                text_color=THEME["primary"],
                cursor="hand2"
            )
            link.pack(side="right")
            if self._link_callback:
                link.bind("<Button-1>", lambda e: self._link_callback())
        
        # Container para conteúdo
        self._content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._content_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))
    
    def add_content(self, widget):
        """Adiciona widget ao conteúdo"""
        widget.pack(in_=self._content_frame, fill="x")
    
    def clear_content(self):
        """Limpa todo o conteúdo"""
        for widget in self._content_frame.winfo_children():
            widget.destroy()


class AlertCard(ctk.CTkFrame):
    """
    Card de alerta/notificação.
    
    Usage:
        alert = AlertCard(parent, title="Estudante em Alerta", message="Requer atenção", variant="danger")
    """
    
    VARIANTS = {
        "danger": {"bg": "#FEE2E2", "fg": "#DC2626", "icon": "🔴"},
        "warning": {"bg": "#FEF3C7", "fg": "#D97706", "icon": "🟠"},
        "success": {"bg": "#DCFCE7", "fg": "#16A34A", "icon": "🟢"},
        "info": {"bg": "#DBEAFE", "fg": "#2563EB", "icon": "🔵"},
    }
    
    def __init__(
        self,
        parent,
        title: str,
        message: str,
        variant: str = "info",
        on_click: Optional[Callable] = None,
        **kwargs
    ):
        colors = self.VARIANTS.get(variant, self.VARIANTS["info"])
        
        super().__init__(
            parent,
            fg_color=colors["bg"],
            corner_radius=RADIUS["input"],
            **kwargs
        )
        
        self._title = title
        self._message = message
        self._colors = colors
        self._on_click = on_click
        
        self._build_ui()
    
    def _build_ui(self):
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=20, pady=15)
        
        ctk.CTkLabel(
            info_frame,
            text=self._title,
            font=font(14, "bold"),
            text_color=THEME["text"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            info_frame,
            text=self._message,
            font=font(12),
            text_color=self._colors["fg"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            self,
            text=self._colors["icon"],
            font=font(13, "bold")
        ).pack(side="right", padx=20)
        
        if self._on_click:
            self.bind("<Button-1>", lambda e: self._on_click())
            info_frame.bind("<Button-1>", lambda e: self._on_click())


class StudentCard(ctk.CTkFrame):
    """
    Card de estudante para listas.
    
    Usage:
        card = StudentCard(parent, name="João Silva", course="Engenharia", on_click=callback)
    """
    
    def __init__(
        self,
        parent,
        name: str,
        course: Optional[str] = None,
        student_id: Optional[int] = None,
        on_click: Optional[Callable[[Dict[str, Any]], None]] = None,
        selected: bool = False,
        **kwargs
    ):
        super().__init__(
            parent,
            fg_color=THEME["purple_light"] if selected else THEME["card"],
            corner_radius=RADIUS["input"],
            border_width=1,
            border_color=THEME["border"],
            cursor="hand2",
            **kwargs
        )
        
        self._name = name
        self._course = course
        self._student_id = student_id
        self._on_click = on_click
        self._selected = selected
        
        self._build_ui()
    
    def _build_ui(self):
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(fill="x", padx=15, pady=10)
        
        # Iniciais (avatar)
        initials = "".join([n[0] for n in self._name.split()[:2]]).upper()
        
        avatar = ctk.CTkFrame(
            info,
            width=36,
            height=36,
            fg_color=THEME["purple_light"],
            corner_radius=18
        )
        avatar.pack(side="left", padx=(0, 10))
        avatar.pack_propagate(False)
        
        ctk.CTkLabel(
            avatar,
            text=initials,
            font=font(12, "bold"),
            text_color=THEME["primary"]
        ).place(relx=0.5, rely=0.5, anchor="center")
        
        # Textos
        text_frame = ctk.CTkFrame(info, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            text_frame,
            text=self._name,
            font=font(13, "bold"),
            text_color=THEME["text"]
        ).pack(anchor="w")
        
        if self._course:
            ctk.CTkLabel(
                text_frame,
                text=self._course,
                font=font(11),
                text_color=THEME["text_muted"]
            ).pack(anchor="w")
        
        # Bind click
        if self._on_click:
            self.bind("<Button-1>", self._handle_click)
            for child in self.winfo_children():
                child.bind("<Button-1>", self._handle_click)
                for sub in child.winfo_children():
                    sub.bind("<Button-1>", self._handle_click)
    
    def _handle_click(self, event):
        if self._on_click:
            self._on_click({
                'id': self._student_id,
                'name': self._name,
                'course': self._course
            })
    
    def set_selected(self, selected: bool):
        """Altera estado de seleção"""
        self._selected = selected
        self.configure(fg_color=THEME["purple_light"] if selected else THEME["card"])


class HistoryCard(ctk.CTkFrame):
    """
    Card para histórico de registros.
    
    Usage:
        card = HistoryCard(
            parent,
            title="Orientação de Estudos",
            date="2026-02-20",
            tags=["Estudos", "Rotina"],
            on_view=callback_view,
            on_edit=callback_edit
        )
    """
    
    def __init__(
        self,
        parent,
        title: str,
        date: Optional[str] = None,
        tags: Optional[list] = None,
        preview: Optional[str] = None,
        on_view: Optional[Callable] = None,
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(
            parent,
            fg_color=THEME["card"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=THEME["border"],
            **kwargs
        )
        
        self._title = title
        self._date = date
        self._tags = tags or []
        self._preview = preview
        self._on_view = on_view
        self._on_edit = on_edit
        self._on_delete = on_delete
        
        self._build_ui()
    
    def _build_ui(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=12)
        
        # Data (círculo)
        if self._date:
            day = self._extract_day(self._date)
            date_circle = ctk.CTkFrame(
                inner,
                width=40,
                height=40,
                fg_color=THEME["purple_light"],
                corner_radius=20
            )
            date_circle.pack(side="left", padx=(0, 12))
            date_circle.pack_propagate(False)
            ctk.CTkLabel(
                date_circle,
                text=day,
                font=font(14, "bold"),
                text_color=THEME["primary"]
            ).place(relx=0.5, rely=0.5, anchor="center")
        
        # Info
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            info,
            text=self._title,
            font=font(14, "bold"),
            text_color=THEME["text"]
        ).pack(anchor="w")
        
        # Tags
        if self._tags:
            tags_frame = ctk.CTkFrame(info, fg_color="transparent")
            tags_frame.pack(anchor="w")
            for tag in self._tags[:3]:
                ctk.CTkLabel(
                    tags_frame,
                    text=tag,
                    font=font(10),
                    text_color=THEME["primary"],
                    fg_color=THEME["purple_light"],
                    corner_radius=4,
                    padx=6,
                    pady=2
                ).pack(side="left", padx=(0, 8))
        
        # Preview
        if self._preview:
            preview_text = self._preview[:100] + "..." if len(self._preview) > 100 else self._preview
            ctk.CTkLabel(
                info,
                text=preview_text,
                font=font(10),
                text_color=THEME["text_muted"],
                wraplength=300,
                justify="left"
            ).pack(anchor="w", pady=(4, 0))
        
        # Botões
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(side="right")
        
        if self._on_view:
            ctk.CTkButton(
                btn_frame,
                text="Ver",
                width=50,
                height=28,
                fg_color=THEME["bg_alt"],
                text_color=THEME["primary"],
                font=font(10),
                command=self._on_view
            ).pack(side="left", padx=(0, 4))
        
        if self._on_edit:
            ctk.CTkButton(
                btn_frame,
                text="Editar",
                width=50,
                height=28,
                fg_color=THEME["primary"],
                text_color="white",
                font=font(10),
                command=self._on_edit
            ).pack(side="left", padx=(0, 4))
        
        if self._on_delete:
            ctk.CTkButton(
                btn_frame,
                text="Excluir",
                width=55,
                height=28,
                fg_color="transparent",
                text_color="red",
                font=font(10),
                border_width=1,
                border_color=THEME["border"],
                command=self._on_delete
            ).pack(side="left")
    
    @staticmethod
    def _extract_day(date_str: str) -> str:
        """Extrai o dia de uma string de data"""
        try:
            from datetime import datetime
            if 'T' in date_str:
                date_obj = datetime.fromisoformat(date_str.replace('Z', ''))
            else:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return str(date_obj.day)
        except:
            return '?'
