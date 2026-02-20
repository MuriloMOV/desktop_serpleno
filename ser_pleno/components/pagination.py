"""
Componentes de Navegação e Paginação para CustomTkinter
"""
import customtkinter as ctk
from typing import Optional, Callable, List, Any
from ui_theme import THEME, RADIUS, font


class PaginationControl(ctk.CTkFrame):
    """
    Componente de paginação reutilizável.
    
    Usage:
        pagination = PaginationControl(
            parent,
            total_items=100,
            items_per_page=10,
            on_page_change=callback
        )
        
        # Atualizar total de itens
        pagination.update_total(200)
        
        # Obter página atual
        current_page = pagination.get_current_page()
    """
    
    def __init__(
        self,
        parent,
        total_items: int = 0,
        items_per_page: int = 10,
        current_page: int = 1,
        on_page_change: Optional[Callable[[int, int], None]] = None,
        show_items_selector: bool = True,
        items_per_page_options: Optional[List[int]] = None,
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self._total_items = total_items
        self._items_per_page = items_per_page
        self._current_page = current_page
        self._on_page_change = on_page_change
        self._show_items_selector = show_items_selector
        self._items_options = items_per_page_options or [10, 25, 50, 100]
        
        self._total_pages = 0
        self._page_label: Optional[ctk.CTkLabel] = None
        self._prev_btn: Optional[ctk.CTkButton] = None
        self._next_btn: Optional[ctk.CTkButton] = None
        self._first_btn: Optional[ctk.CTkButton] = None
        self._last_btn: Optional[ctk.CTkButton] = None
        self._items_selector: Optional[ctk.CTkOptionMenu] = None
        
        self._calculate_pages()
        self._build_ui()
    
    def _calculate_pages(self):
        """Calcula o total de páginas"""
        if self._items_per_page > 0:
            self._total_pages = max(1, (self._total_items + self._items_per_page - 1) // self._items_per_page)
        else:
            self._total_pages = 1
        
        # Garante que a página atual está dentro do range
        if self._current_page > self._total_pages:
            self._current_page = self._total_pages
        if self._current_page < 1:
            self._current_page = 1
    
    def _build_ui(self):
        """Constrói a interface do componente"""
        # Container principal
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", pady=8)
        
        # Lado esquerdo - Informações
        info_frame = ctk.CTkFrame(container, fg_color="transparent")
        info_frame.pack(side="left")
        
        start_item = (self._current_page - 1) * self._items_per_page + 1
        end_item = min(self._current_page * self._items_per_page, self._total_items)
        
        if self._total_items > 0:
            info_text = f"Mostrando {start_item}-{end_item} de {self._total_items} itens"
        else:
            info_text = "Nenhum item"
        
        self._info_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=font(11),
            text_color=THEME["text_muted"]
        )
        self._info_label.pack(side="left")
        
        # Lado direito - Controles
        controls_frame = ctk.CTkFrame(container, fg_color="transparent")
        controls_frame.pack(side="right")
        
        # Seletor de itens por página
        if self._show_items_selector:
            selector_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
            selector_frame.pack(side="left", padx=(0, 16))
            
            ctk.CTkLabel(
                selector_frame,
                text="Itens por página:",
                font=font(11),
                text_color=THEME["text_muted"]
            ).pack(side="left", padx=(0, 8))
            
            self._items_selector = ctk.CTkOptionMenu(
                selector_frame,
                values=[str(x) for x in self._items_options],
                width=70,
                height=32,
                font=font(11),
                fg_color=THEME["card"],
                button_color=THEME["card"],
                button_hover_color=THEME["bg_alt"],
                command=self._on_items_per_page_change
            )
            self._items_selector.set(str(self._items_per_page))
            self._items_selector.pack(side="left")
        
        # Botões de navegação
        nav_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        nav_frame.pack(side="left")
        
        # Botão primeira página
        self._first_btn = ctk.CTkButton(
            nav_frame,
            text="⟪",
            width=32,
            height=32,
            font=font(12),
            fg_color=THEME["bg_alt"],
            text_color=THEME["text"],
            hover_color=THEME["border"],
            command=self._go_to_first
        )
        self._first_btn.pack(side="left", padx=2)
        
        # Botão página anterior
        self._prev_btn = ctk.CTkButton(
            nav_frame,
            text="◀",
            width=32,
            height=32,
            font=font(12),
            fg_color=THEME["bg_alt"],
            text_color=THEME["text"],
            hover_color=THEME["border"],
            command=self._go_to_prev
        )
        self._prev_btn.pack(side="left", padx=2)
        
        # Label da página atual
        self._page_label = ctk.CTkLabel(
            nav_frame,
            text=f" {self._current_page} / {self._total_pages} ",
            font=font(11, "bold"),
            text_color=THEME["text"]
        )
        self._page_label.pack(side="left", padx=8)
        
        # Botão próxima página
        self._next_btn = ctk.CTkButton(
            nav_frame,
            text="▶",
            width=32,
            height=32,
            font=font(12),
            fg_color=THEME["bg_alt"],
            text_color=THEME["text"],
            hover_color=THEME["border"],
            command=self._go_to_next
        )
        self._next_btn.pack(side="left", padx=2)
        
        # Botão última página
        self._last_btn = ctk.CTkButton(
            nav_frame,
            text="⟫",
            width=32,
            height=32,
            font=font(12),
            fg_color=THEME["bg_alt"],
            text_color=THEME["text"],
            hover_color=THEME["border"],
            command=self._go_to_last
        )
        self._last_btn.pack(side="left", padx=2)
        
        self._update_buttons_state()
    
    def _update_buttons_state(self):
        """Atualiza o estado dos botões de navegação"""
        # Desabilita botões quando na primeira página
        if self._current_page <= 1:
            self._first_btn.configure(state="disabled", fg_color=THEME["border"])
            self._prev_btn.configure(state="disabled", fg_color=THEME["border"])
        else:
            self._first_btn.configure(state="normal", fg_color=THEME["bg_alt"])
            self._prev_btn.configure(state="normal", fg_color=THEME["bg_alt"])
        
        # Desabilita botões quando na última página
        if self._current_page >= self._total_pages:
            self._next_btn.configure(state="disabled", fg_color=THEME["border"])
            self._last_btn.configure(state="disabled", fg_color=THEME["border"])
        else:
            self._next_btn.configure(state="normal", fg_color=THEME["bg_alt"])
            self._last_btn.configure(state="normal", fg_color=THEME["bg_alt"])
        
        # Atualiza label
        self._page_label.configure(text=f" {self._current_page} / {self._total_pages} ")
        
        # Atualiza info
        start_item = (self._current_page - 1) * self._items_per_page + 1
        end_item = min(self._current_page * self._items_per_page, self._total_items)
        
        if self._total_items > 0:
            info_text = f"Mostrando {start_item}-{end_item} de {self._total_items} itens"
        else:
            info_text = "Nenhum item"
        
        self._info_label.configure(text=info_text)
    
    def _on_items_per_page_change(self, value: str):
        """Handler para mudança de itens por página"""
        self._items_per_page = int(value)
        self._current_page = 1
        self._calculate_pages()
        self._update_buttons_state()
        
        if self._on_page_change:
            self._on_page_change(self._current_page, self._items_per_page)
    
    def _go_to_first(self):
        """Vai para a primeira página"""
        if self._current_page > 1:
            self._current_page = 1
            self._update_buttons_state()
            if self._on_page_change:
                self._on_page_change(self._current_page, self._items_per_page)
    
    def _go_to_prev(self):
        """Vai para a página anterior"""
        if self._current_page > 1:
            self._current_page -= 1
            self._update_buttons_state()
            if self._on_page_change:
                self._on_page_change(self._current_page, self._items_per_page)
    
    def _go_to_next(self):
        """Vai para a próxima página"""
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._update_buttons_state()
            if self._on_page_change:
                self._on_page_change(self._current_page, self._items_per_page)
    
    def _go_to_last(self):
        """Vai para a última página"""
        if self._current_page < self._total_pages:
            self._current_page = self._total_pages
            self._update_buttons_state()
            if self._on_page_change:
                self._on_page_change(self._current_page, self._items_per_page)
    
    def update_total(self, total_items: int):
        """Atualiza o total de itens"""
        self._total_items = total_items
        self._calculate_pages()
        self._update_buttons_state()
    
    def get_current_page(self) -> int:
        """Retorna a página atual"""
        return self._current_page
    
    def get_items_per_page(self) -> int:
        """Retorna itens por página"""
        return self._items_per_page
    
    def get_offset(self) -> int:
        """Retorna o offset para queries SQL"""
        return (self._current_page - 1) * self._items_per_page
    
    def set_page(self, page: int):
        """Define a página atual"""
        if 1 <= page <= self._total_pages:
            self._current_page = page
            self._update_buttons_state()
    
    def reset(self):
        """Reseta para a primeira página"""
        self._current_page = 1
        self._update_buttons_state()


class PageSelector(ctk.CTkFrame):
    """
    Seletor de página compacto para espaços menores.
    
    Usage:
        selector = PageSelector(parent, total_pages=10, on_page_change=callback)
    """
    
    def __init__(
        self,
        parent,
        total_pages: int = 1,
        current_page: int = 1,
        on_page_change: Optional[Callable[[int], None]] = None,
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self._total_pages = total_pages
        self._current_page = current_page
        self._on_page_change = on_page_change
        
        self._build_ui()
    
    def _build_ui(self):
        # Botão anterior
        self._prev_btn = ctk.CTkButton(
            self,
            text="◀",
            width=28,
            height=28,
            font=font(10),
            fg_color=THEME["bg_alt"],
            text_color=THEME["text"],
            hover_color=THEME["border"],
            command=self._go_prev
        )
        self._prev_btn.pack(side="left", padx=2)
        
        # Seletor de página
        self._page_entry = ctk.CTkEntry(
            self,
            width=40,
            height=28,
            font=font(11),
            justify="center"
        )
        self._page_entry.insert(0, str(self._current_page))
        self._page_entry.pack(side="left", padx=4)
        self._page_entry.bind("<Return>", self._on_entry_change)
        
        # Label total
        self._total_label = ctk.CTkLabel(
            self,
            text=f"/ {self._total_pages}",
            font=font(11),
            text_color=THEME["text_muted"]
        )
        self._total_label.pack(side="left")
        
        # Botão próximo
        self._next_btn = ctk.CTkButton(
            self,
            text="▶",
            width=28,
            height=28,
            font=font(10),
            fg_color=THEME["bg_alt"],
            text_color=THEME["text"],
            hover_color=THEME["border"],
            command=self._go_next
        )
        self._next_btn.pack(side="left", padx=2)
        
        self._update_state()
    
    def _update_state(self):
        """Atualiza estado dos botões"""
        self._prev_btn.configure(
            state="disabled" if self._current_page <= 1 else "normal"
        )
        self._next_btn.configure(
            state="disabled" if self._current_page >= self._total_pages else "normal"
        )
        self._total_label.configure(text=f"/ {self._total_pages}")
    
    def _go_prev(self):
        if self._current_page > 1:
            self._current_page -= 1
            self._update_entry()
            self._update_state()
            if self._on_page_change:
                self._on_page_change(self._current_page)
    
    def _go_next(self):
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._update_entry()
            self._update_state()
            if self._on_page_change:
                self._on_page_change(self._current_page)
    
    def _on_entry_change(self, event):
        try:
            page = int(self._page_entry.get())
            if 1 <= page <= self._total_pages:
                self._current_page = page
                self._update_state()
                if self._on_page_change:
                    self._on_page_change(self._current_page)
        except ValueError:
            self._update_entry()
    
    def _update_entry(self):
        self._page_entry.delete(0, "end")
        self._page_entry.insert(0, str(self._current_page))
    
    def set_total_pages(self, total: int):
        self._total_pages = max(1, total)
        if self._current_page > self._total_pages:
            self._current_page = self._total_pages
        self._update_entry()
        self._update_state()
    
    def get_current_page(self) -> int:
        return self._current_page
