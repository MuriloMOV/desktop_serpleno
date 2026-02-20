"""
UI de Importação de Dados para o Desktop CustomTkinter
Dialog para importar dados de arquivos CSV, Excel e JSON
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional, Dict, Any, List, Callable
import os
import threading

from ui_theme import THEME, RADIUS, font, SPACING
from services.importacao import servico_importacao, ImportStatus


class ImportDialog(ctk.CTkToplevel):
    """
    Dialog para importação de dados.
    
    Usage:
        dialog = ImportDialog(parent, entity_type="estudantes", on_complete=callback)
    """
    
    def __init__(
        self,
        parent,
        entity_type: str = "estudantes",
        on_complete: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        super().__init__(parent)
        
        self._entity_type = entity_type
        self._on_complete = on_complete
        self._file_path: Optional[str] = None
        self._preview_data: Optional[Dict[str, Any]] = None
        self._import_thread: Optional[threading.Thread] = None
        
        self._setup_window()
        self._build_ui()
    
    def _setup_window(self):
        """Configura a janela"""
        self.title(f"Importar {self._entity_type.title()}")
        self.geometry("800x600")
        self.resizable(True, True)
        
        # Centraliza na tela
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 800) // 2
        y = (self.winfo_screenheight() - 600) // 2
        self.geometry(f"+{x}+{y}")
        
        # Modal
        self.transient(self.master)
        self.grab_set()
    
    def _build_ui(self):
        """Constrói a interface"""
        # Container principal
        main_frame = ctk.CTkFrame(self, fg_color=THEME["bg"])
        main_frame.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=SPACING["page_y"])
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text=f"Importar {self._entity_type.title()}",
            font=font(20, "bold"),
            text_color=THEME["text"]
        )
        title_label.pack(anchor="w", pady=(0, SPACING["section_gap"]))
        
        # Seção de seleção de arquivo
        file_section = ctk.CTkFrame(main_frame, fg_color=THEME["card"], corner_radius=RADIUS["card"])
        file_section.pack(fill="x", pady=(0, SPACING["item_gap"]))
        
        file_header = ctk.CTkLabel(
            file_section,
            text="1. Selecione o Arquivo",
            font=font(14, "bold"),
            text_color=THEME["text"]
        )
        file_header.pack(anchor="w", padx=SPACING["card_pad"], pady=(SPACING["card_pad"], 8))
        
        file_frame = ctk.CTkFrame(file_section, fg_color="transparent")
        file_frame.pack(fill="x", padx=SPACING["card_pad"], pady=(0, SPACING["card_pad"]))
        
        self._file_entry = ctk.CTkEntry(
            file_frame,
            placeholder_text="Nenhum arquivo selecionado",
            height=40,
            fg_color=THEME["bg_alt"],
            border_color=THEME["border"],
            corner_radius=RADIUS["input"]
        )
        self._file_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        browse_btn = ctk.CTkButton(
            file_frame,
            text="Procurar",
            width=100,
            height=40,
            font=font(12),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            command=self._browse_file
        )
        browse_btn.pack(side="right")
        
        # Formatos suportados
        formats_label = ctk.CTkLabel(
            file_section,
            text="Formatos suportados: CSV (.csv), Excel (.xlsx, .xls), JSON (.json)",
            font=font(10),
            text_color=THEME["text_muted"]
        )
        formats_label.pack(anchor="w", padx=SPACING["card_pad"], pady=(0, SPACING["card_pad"]))
        
        # Seção de preview
        preview_section = ctk.CTkFrame(main_frame, fg_color=THEME["card"], corner_radius=RADIUS["card"])
        preview_section.pack(fill="both", expand=True, pady=(0, SPACING["item_gap"]))
        
        preview_header = ctk.CTkLabel(
            preview_section,
            text="2. Preview dos Dados",
            font=font(14, "bold"),
            text_color=THEME["text"]
        )
        preview_header.pack(anchor="w", padx=SPACING["card_pad"], pady=(SPACING["card_pad"], 8))
        
        # Info do arquivo
        self._info_frame = ctk.CTkFrame(preview_section, fg_color="transparent")
        self._info_frame.pack(fill="x", padx=SPACING["card_pad"])
        
        self._info_label = ctk.CTkLabel(
            self._info_frame,
            text="Selecione um arquivo para visualizar o preview",
            font=font(11),
            text_color=THEME["text_muted"]
        )
        self._info_label.pack(anchor="w")
        
        # Tabela de preview
        self._preview_frame = ctk.CTkScrollableFrame(
            preview_section,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["input"]
        )
        self._preview_frame.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=(8, SPACING["card_pad"]))
        
        # Mapeamento de colunas
        mapping_section = ctk.CTkFrame(main_frame, fg_color=THEME["card"], corner_radius=RADIUS["card"])
        mapping_section.pack(fill="x", pady=(0, SPACING["item_gap"]))
        
        mapping_header = ctk.CTkLabel(
            mapping_section,
            text="3. Mapeamento de Colunas",
            font=font(14, "bold"),
            text_color=THEME["text"]
        )
        mapping_header.pack(anchor="w", padx=SPACING["card_pad"], pady=(SPACING["card_pad"], 8))
        
        self._mapping_frame = ctk.CTkFrame(mapping_section, fg_color="transparent")
        self._mapping_frame.pack(fill="x", padx=SPACING["card_pad"], pady=(0, SPACING["card_pad"]))
        
        # Opções
        options_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        options_frame.pack(fill="x", pady=(0, SPACING["section_gap"]))
        
        self._skip_duplicates_var = ctk.BooleanVar(value=True)
        skip_duplicates_cb = ctk.CTkCheckBox(
            options_frame,
            text="Pular registros duplicados",
            variable=self._skip_duplicates_var,
            font=font(11),
            border_color=THEME["border"],
            checkmark_color=THEME["primary"]
        )
        skip_duplicates_cb.pack(side="left")
        
        self._update_existing_var = ctk.BooleanVar(value=False)
        update_existing_cb = ctk.CTkCheckBox(
            options_frame,
            text="Atualizar registros existentes",
            variable=self._update_existing_var,
            font=font(11),
            border_color=THEME["border"],
            checkmark_color=THEME["primary"]
        )
        update_existing_cb.pack(side="left", padx=(20, 0))
        
        # Barra de progresso
        self._progress_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self._progress_frame.pack(fill="x", pady=(0, SPACING["item_gap"]))
        
        self._progress_bar = ctk.CTkProgressBar(
            self._progress_frame,
            height=8,
            corner_radius=4,
            fg_color=THEME["bg_alt"],
            progress_color=THEME["primary"]
        )
        self._progress_bar.set(0)
        self._progress_bar.pack(fill="x")
        
        self._progress_label = ctk.CTkLabel(
            self._progress_frame,
            text="",
            font=font(10),
            text_color=THEME["text_muted"]
        )
        self._progress_label.pack(anchor="w", pady=(4, 0))
        
        # Botões
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x")
        
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Cancelar",
            width=100,
            height=40,
            font=font(12),
            fg_color=THEME["bg_alt"],
            text_color=THEME["text"],
            hover_color=THEME["border"],
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=(8, 0))
        
        self._import_btn = ctk.CTkButton(
            buttons_frame,
            text="Importar",
            width=120,
            height=40,
            font=font(12, "bold"),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            command=self._start_import,
            state="disabled"
        )
        self._import_btn.pack(side="right")
    
    def _browse_file(self):
        """Abre diálogo para selecionar arquivo"""
        filetypes = [
            ("Todos os arquivos", "*.csv *.xlsx *.xls *.json"),
            ("CSV", "*.csv"),
            ("Excel", "*.xlsx *.xls"),
            ("JSON", "*.json"),
        ]
        
        file_path = filedialog.askopenfilename(
            title=f"Selecionar arquivo de {self._entity_type}",
            filetypes=filetypes
        )
        
        if file_path:
            self._file_path = file_path
            self._file_entry.delete(0, "end")
            self._file_entry.insert(0, os.path.basename(file_path))
            self._load_preview()
    
    def _load_preview(self):
        """Carrega preview do arquivo"""
        if not self._file_path:
            return
        
        self._progress_label.configure(text="Carregando preview...")
        
        def load():
            try:
                self._preview_data = servico_importacao.preview_import(
                    self._file_path,
                    self._entity_type
                )
                self.after(0, self._show_preview)
            except Exception as e:
                self.after(0, lambda: self._show_error(str(e)))
        
        threading.Thread(target=load, daemon=True).start()
    
    def _show_preview(self):
        """Exibe preview dos dados"""
        if not self._preview_data or not self._preview_data.get("success"):
            self._show_error(self._preview_data.get("error", "Erro ao carregar preview"))
            return
        
        # Atualiza info
        total_rows = self._preview_data.get("total_rows", 0)
        headers = self._preview_data.get("headers", [])
        mapping = self._preview_data.get("detected_mapping", {})
        
        self._info_label.configure(
            text=f"Total de linhas: {total_rows} | Colunas detectadas: {len(headers)}"
        )
        
        # Limpa preview anterior
        for widget in self._preview_frame.winfo_children():
            widget.destroy()
        
        # Cria tabela de preview
        if headers:
            # Header
            header_frame = ctk.CTkFrame(self._preview_frame, fg_color=THEME["primary_light"])
            header_frame.pack(fill="x", pady=(0, 4))
            
            for i, header in enumerate(headers[:6]):  # Limita a 6 colunas
                label = ctk.CTkLabel(
                    header_frame,
                    text=header,
                    font=font(10, "bold"),
                    text_color=THEME["text"],
                    width=100
                )
                label.pack(side="left", padx=8, pady=6)
            
            # Dados (primeiras 5 linhas)
            sample_data = self._preview_data.get("sample_data", [])
            for row in sample_data[:5]:
                row_frame = ctk.CTkFrame(self._preview_frame, fg_color=THEME["card"])
                row_frame.pack(fill="x", pady=1)
                
                for header in headers[:6]:
                    value = str(row.get(header, ""))[:20]
                    label = ctk.CTkLabel(
                        row_frame,
                        text=value,
                        font=font(10),
                        text_color=THEME["text"],
                        width=100
                    )
                    label.pack(side="left", padx=8, pady=4)
        
        # Mostra mapeamento detectado
        self._show_mapping(mapping)
        
        # Habilita botão de importar
        self._import_btn.configure(state="normal")
        self._progress_label.configure(text="")
    
    def _show_mapping(self, mapping: Dict[str, str]):
        """Exibe mapeamento de colunas"""
        for widget in self._mapping_frame.winfo_children():
            widget.destroy()
        
        if not mapping:
            label = ctk.CTkLabel(
                self._mapping_frame,
                text="Nenhum mapeamento automático detectado",
                font=font(11),
                text_color=THEME["text_muted"]
            )
            label.pack(anchor="w")
            return
        
        for system_field, file_column in mapping.items():
            row_frame = ctk.CTkFrame(self._mapping_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            
            field_label = ctk.CTkLabel(
                row_frame,
                text=system_field,
                font=font(11),
                text_color=THEME["text"],
                width=150,
                anchor="w"
            )
            field_label.pack(side="left")
            
            arrow_label = ctk.CTkLabel(
                row_frame,
                text="←",
                font=font(11),
                text_color=THEME["text_muted"]
            )
            arrow_label.pack(side="left", padx=8)
            
            column_label = ctk.CTkLabel(
                row_frame,
                text=file_column,
                font=font(11, "bold"),
                text_color=THEME["primary"]
            )
            column_label.pack(side="left")
    
    def _show_error(self, message: str):
        """Exibe mensagem de erro"""
        self._progress_label.configure(text=f"Erro: {message}")
        self._import_btn.configure(state="disabled")
    
    def _start_import(self):
        """Inicia a importação"""
        if not self._file_path:
            return
        
        self._import_btn.configure(state="disabled")
        self._progress_bar.set(0)
        self._progress_label.configure(text="Importando...")
        
        def import_data():
            try:
                # Configura callback de progresso
                servico_importacao.set_progress_callback(self._update_progress)
                
                # Executa importação
                if self._entity_type == "estudantes":
                    report = servico_importacao.importar_estudantes(
                        self._file_path,
                        skip_duplicates=self._skip_duplicates_var.get(),
                        update_existing=self._update_existing_var.get()
                    )
                elif self._entity_type == "agendamentos":
                    report = servico_importacao.importar_agendamentos(self._file_path)
                elif self._entity_type == "orientacoes":
                    report = servico_importacao.importar_orientacoes(self._file_path)
                else:
                    report = servico_importacao.importar_estudantes(self._file_path)
                
                self.after(0, lambda: self._import_complete(report))
                
            except Exception as e:
                self.after(0, lambda: self._show_error(str(e)))
        
        self._import_thread = threading.Thread(target=import_data, daemon=True)
        self._import_thread.start()
    
    def _update_progress(self, current: int, total: int, message: str):
        """Atualiza barra de progresso"""
        progress = current / total if total > 0 else 0
        self.after(0, lambda: self._progress_bar.set(progress))
        self.after(0, lambda: self._progress_label.configure(text=message))
    
    def _import_complete(self, report):
        """Chamado quando a importação termina"""
        self._progress_bar.set(1)
        
        # Mostra resumo
        summary = report.to_dict()
        message = (
            f"Importação concluída!\n\n"
            f"Sucesso: {summary['success_count']}\n"
            f"Avisos: {summary['warning_count']}\n"
            f"Erros: {summary['error_count']}\n"
            f"Ignorados: {summary['skipped_count']}\n\n"
            f"Duração: {summary['duration_seconds']:.2f}s"
        )
        
        if summary['error_count'] > 0:
            messagebox.showwarning("Importação Concluída com Avisos", message)
        else:
            messagebox.showinfo("Importação Concluída", message)
        
        # Callback
        if self._on_complete:
            self._on_complete(summary)
        
        self.destroy()


class ImportButton(ctk.CTkButton):
    """
    Botão de importação que abre o dialog.
    
    Usage:
        btn = ImportButton(parent, entity_type="estudantes", on_complete=callback)
    """
    
    def __init__(
        self,
        parent,
        entity_type: str = "estudantes",
        on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
        **kwargs
    ):
        defaults = {
            "text": "📥 Importar",
            "font": font(12),
            "fg_color": THEME["success"],
            "hover_color": "#0EA472",
            "height": 36,
            "corner_radius": RADIUS["button"],
        }
        defaults.update(kwargs)
        
        super().__init__(parent, command=self._open_dialog, **defaults)
        
        self._entity_type = entity_type
        self._on_complete = on_complete
        self._dialog: Optional[ImportDialog] = None
    
    def _open_dialog(self):
        self._dialog = ImportDialog(
            self.winfo_toplevel(),
            entity_type=self._entity_type,
            on_complete=self._on_complete
        )
