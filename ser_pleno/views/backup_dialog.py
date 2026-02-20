"""
UI de Backup e Restore para o Desktop CustomTkinter
Dialog para gerenciar backups do sistema
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional, Dict, Any, List, Callable
import os
import threading
from datetime import datetime

from ui_theme import THEME, RADIUS, font, SPACING
from services.backup import servico_backup, BackupType, BackupStatus


class BackupDialog(ctk.CTkToplevel):
    """
    Dialog para gerenciamento de backups.
    
    Usage:
        dialog = BackupDialog(parent)
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self._selected_backup_id: Optional[str] = None
        self._backups: List[Any] = []
        
        self._setup_window()
        self._build_ui()
        self._load_backups()
    
    def _setup_window(self):
        """Configura a janela"""
        self.title("Backup e Restore")
        self.geometry("900x700")
        self.resizable(True, True)
        
        # Centraliza na tela
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 900) // 2
        y = (self.winfo_screenheight() - 700) // 2
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
            text="Backup e Restore",
            font=font(20, "bold"),
            text_color=THEME["text"]
        )
        title_label.pack(anchor="w", pady=(0, SPACING["section_gap"]))
        
        # Seção de ações
        actions_section = ctk.CTkFrame(main_frame, fg_color=THEME["card"], corner_radius=RADIUS["card"])
        actions_section.pack(fill="x", pady=(0, SPACING["item_gap"]))
        
        actions_header = ctk.CTkLabel(
            actions_section,
            text="Criar Backup",
            font=font(14, "bold"),
            text_color=THEME["text"]
        )
        actions_header.pack(anchor="w", padx=SPACING["card_pad"], pady=(SPACING["card_pad"], 8))
        
        actions_frame = ctk.CTkFrame(actions_section, fg_color="transparent")
        actions_frame.pack(fill="x", padx=SPACING["card_pad"], pady=(0, SPACING["card_pad"]))
        
        # Botão backup completo
        full_backup_btn = ctk.CTkButton(
            actions_frame,
            text="💾 Backup Completo",
            width=150,
            height=40,
            font=font(12),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            command=self._create_full_backup
        )
        full_backup_btn.pack(side="left", padx=(0, 8))
        
        # Botão backup incremental
        incremental_backup_btn = ctk.CTkButton(
            actions_frame,
            text="📦 Backup Incremental",
            width=160,
            height=40,
            font=font(12),
            fg_color=THEME["info"],
            hover_color="#2563EB",
            command=self._create_incremental_backup
        )
        incremental_backup_btn.pack(side="left", padx=(0, 8))
        
        # Botão limpar antigos
        cleanup_btn = ctk.CTkButton(
            actions_frame,
            text="🧹 Limpar Antigos",
            width=130,
            height=40,
            font=font(12),
            fg_color=THEME["warning"],
            hover_color="#D97706",
            command=self._cleanup_old_backups
        )
        cleanup_btn.pack(side="left")
        
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
        
        # Seção de backups existentes
        backups_section = ctk.CTkFrame(main_frame, fg_color=THEME["card"], corner_radius=RADIUS["card"])
        backups_section.pack(fill="both", expand=True, pady=(0, SPACING["item_gap"]))
        
        backups_header = ctk.CTkLabel(
            backups_section,
            text="Backups Disponíveis",
            font=font(14, "bold"),
            text_color=THEME["text"]
        )
        backups_header.pack(anchor="w", padx=SPACING["card_pad"], pady=(SPACING["card_pad"], 8))
        
        # Lista de backups
        self._backups_frame = ctk.CTkScrollableFrame(
            backups_section,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["input"]
        )
        self._backups_frame.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=(0, SPACING["card_pad"]))
        
        # Botões de ação
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x")
        
        close_btn = ctk.CTkButton(
            buttons_frame,
            text="Fechar",
            width=100,
            height=40,
            font=font(12),
            fg_color=THEME["bg_alt"],
            text_color=THEME["text"],
            hover_color=THEME["border"],
            command=self.destroy
        )
        close_btn.pack(side="right", padx=(8, 0))
        
        self._restore_btn = ctk.CTkButton(
            buttons_frame,
            text="🔄 Restaurar Selecionado",
            width=160,
            height=40,
            font=font(12, "bold"),
            fg_color=THEME["success"],
            hover_color="#0EA472",
            command=self._restore_backup,
            state="disabled"
        )
        self._restore_btn.pack(side="right", padx=(8, 0))
        
        self._verify_btn = ctk.CTkButton(
            buttons_frame,
            text="✓ Verificar",
            width=100,
            height=40,
            font=font(12),
            fg_color=THEME["info"],
            hover_color="#2563EB",
            command=self._verify_backup,
            state="disabled"
        )
        self._verify_btn.pack(side="right", padx=(8, 0))
        
        self._delete_btn = ctk.CTkButton(
            buttons_frame,
            text="🗑 Excluir",
            width=100,
            height=40,
            font=font(12),
            fg_color=THEME["danger"],
            hover_color="#DC2626",
            command=self._delete_backup,
            state="disabled"
        )
        self._delete_btn.pack(side="right")
    
    def _load_backups(self):
        """Carrega lista de backups"""
        self._backups = servico_backup.list_backups()
        self._show_backups()
    
    def _show_backups(self):
        """Exibe lista de backups"""
        # Limpa lista anterior
        for widget in self._backups_frame.winfo_children():
            widget.destroy()
        
        if not self._backups:
            empty_label = ctk.CTkLabel(
                self._backups_frame,
                text="Nenhum backup encontrado",
                font=font(12),
                text_color=THEME["text_muted"]
            )
            empty_label.pack(pady=20)
            return
        
        for backup in self._backups:
            self._create_backup_row(backup)
    
    def _create_backup_row(self, backup):
        """Cria uma linha para um backup"""
        row_frame = ctk.CTkFrame(
            self._backups_frame,
            fg_color=THEME["card"],
            corner_radius=RADIUS["button"],
            border_width=1,
            border_color=THEME["border"]
        )
        row_frame.pack(fill="x", pady=4, padx=4)
        
        # Bind click
        row_frame.bind("<Button-1>", lambda e, b=backup: self._select_backup(b, row_frame))
        
        # Tipo de backup
        type_colors = {
            BackupType.FULL: THEME["primary"],
            BackupType.INCREMENTAL: THEME["info"],
            BackupType.DATA_ONLY: THEME["warning"],
        }
        
        type_label = ctk.CTkLabel(
            row_frame,
            text=backup.type.value.upper(),
            font=font(10, "bold"),
            text_color=type_colors.get(backup.type, THEME["text"]),
            width=100
        )
        type_label.pack(side="left", padx=8, pady=8)
        type_label.bind("<Button-1>", lambda e, b=backup: self._select_backup(b, row_frame))
        
        # Data
        date_str = backup.created_at.strftime("%d/%m/%Y %H:%M")
        date_label = ctk.CTkLabel(
            row_frame,
            text=date_str,
            font=font(11),
            text_color=THEME["text"],
            width=120
        )
        date_label.pack(side="left", padx=8, pady=8)
        date_label.bind("<Button-1>", lambda e, b=backup: self._select_backup(b, row_frame))
        
        # Tamanho
        size_str = backup._format_size(backup.file_size)
        size_label = ctk.CTkLabel(
            row_frame,
            text=size_str,
            font=font(11),
            text_color=THEME["text_muted"],
            width=80
        )
        size_label.pack(side="left", padx=8, pady=8)
        size_label.bind("<Button-1>", lambda e, b=backup: self._select_backup(b, row_frame))
        
        # Status
        status_colors = {
            BackupStatus.COMPLETED: THEME["success"],
            BackupStatus.FAILED: THEME["danger"],
            BackupStatus.IN_PROGRESS: THEME["warning"],
            BackupStatus.PENDING: THEME["text_muted"],
        }
        
        status_label = ctk.CTkLabel(
            row_frame,
            text=backup.status.value.upper(),
            font=font(10),
            text_color=status_colors.get(backup.status, THEME["text_muted"]),
            width=100
        )
        status_label.pack(side="left", padx=8, pady=8)
        status_label.bind("<Button-1>", lambda e, b=backup: self._select_backup(b, row_frame))
        
        # Tabelas
        if backup.tables_included:
            tables_str = f"{len(backup.tables_included)} tabelas"
        else:
            tables_str = "-"
        
        tables_label = ctk.CTkLabel(
            row_frame,
            text=tables_str,
            font=font(10),
            text_color=THEME["text_muted"],
            width=80
        )
        tables_label.pack(side="left", padx=8, pady=8)
        tables_label.bind("<Button-1>", lambda e, b=backup: self._select_backup(b, row_frame))
        
        # Armazena referência
        row_frame._backup_id = backup.id
    
    def _select_backup(self, backup, row_frame):
        """Seleciona um backup"""
        self._selected_backup_id = backup.id
        
        # Atualiza visual
        for widget in self._backups_frame.winfo_children():
            widget.configure(border_color=THEME["border"])
        
        row_frame.configure(border_color=THEME["primary"])
        
        # Habilita botões
        self._restore_btn.configure(state="normal")
        self._verify_btn.configure(state="normal")
        self._delete_btn.configure(state="normal")
    
    def _create_full_backup(self):
        """Cria backup completo"""
        self._progress_label.configure(text="Criando backup completo...")
        self._progress_bar.set(0)
        
        def create():
            servico_backup.set_progress_callback(self._update_progress)
            backup_info = servico_backup.create_full_backup(
                include_files=True,
                compress=True
            )
            self.after(0, lambda: self._backup_complete(backup_info))
        
        threading.Thread(target=create, daemon=True).start()
    
    def _create_incremental_backup(self):
        """Cria backup incremental"""
        self._progress_label.configure(text="Criando backup incremental...")
        self._progress_bar.set(0)
        
        def create():
            from datetime import datetime, timedelta
            since = datetime.now() - timedelta(days=7)
            servico_backup.set_progress_callback(self._update_progress)
            backup_info = servico_backup.create_incremental_backup(since=since, compress=True)
            self.after(0, lambda: self._backup_complete(backup_info))
        
        threading.Thread(target=create, daemon=True).start()
    
    def _backup_complete(self, backup_info):
        """Chamado quando backup termina"""
        if backup_info.status == BackupStatus.COMPLETED:
            self._progress_label.configure(text=f"Backup criado: {backup_info.id}")
            self._progress_bar.set(1)
            messagebox.showinfo(
                "Backup Concluído",
                f"Backup criado com sucesso!\n\n"
                f"ID: {backup_info.id}\n"
                f"Tamanho: {backup_info._format_size(backup_info.file_size)}"
            )
            self._load_backups()
        else:
            self._progress_label.configure(text="Erro ao criar backup")
            messagebox.showerror(
                "Erro no Backup",
                f"Erro ao criar backup:\n{backup_info.error_message}"
            )
    
    def _restore_backup(self):
        """Restaura backup selecionado"""
        if not self._selected_backup_id:
            return
        
        # Confirmação
        if not messagebox.askyesno(
            "Confirmar Restore",
            f"Tem certeza que deseja restaurar o backup {self._selected_backup_id}?\n\n"
            "Esta ação pode sobrescrever dados existentes."
        ):
            return
        
        self._progress_label.configure(text="Restaurando backup...")
        self._progress_bar.set(0)
        
        def restore():
            result = servico_backup.restore_backup(self._selected_backup_id)
            self.after(0, lambda: self._restore_complete(result))
        
        threading.Thread(target=restore, daemon=True).start()
    
    def _restore_complete(self, result):
        """Chamado quando restore termina"""
        if result.success:
            self._progress_label.configure(text="Restore concluído")
            self._progress_bar.set(1)
            messagebox.showinfo(
                "Restore Concluído",
                f"Backup restaurado com sucesso!\n\n"
                f"Tabelas restauradas: {len(result.tables_restored)}\n"
                f"Total de registros: {sum(result.records_restored.values())}"
            )
        else:
            self._progress_label.configure(text="Erro no restore")
            messagebox.showerror(
                "Erro no Restore",
                f"Erro ao restaurar backup:\n" + "\n".join(result.errors)
            )
    
    def _verify_backup(self):
        """Verifica integridade do backup"""
        if not self._selected_backup_id:
            return
        
        self._progress_label.configure(text="Verificando backup...")
        
        def verify():
            result = servico_backup.verify_backup(self._selected_backup_id)
            self.after(0, lambda: self._verify_complete(result))
        
        threading.Thread(target=verify, daemon=True).start()
    
    def _verify_complete(self, result):
        """Chamado quando verificação termina"""
        if result.get("valid"):
            messagebox.showinfo(
                "Verificação Concluída",
                f"Backup válido!\n\n"
                f"Tabelas: {result.get('tables_count', 0)}\n"
                f"Tabelas: {', '.join(result.get('tables', []))}"
            )
        else:
            messagebox.showwarning(
                "Verificação Concluída",
                f"Backup com problemas!\n\n"
                f"Erros: {', '.join(result.get('errors', []))}\n"
                f"Avisos: {', '.join(result.get('warnings', []))}"
            )
        self._progress_label.configure(text="")
    
    def _delete_backup(self):
        """Exclui backup selecionado"""
        if not self._selected_backup_id:
            return
        
        if not messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o backup {self._selected_backup_id}?\n\n"
            "Esta ação não pode ser desfeita."
        ):
            return
        
        if servico_backup.delete_backup(self._selected_backup_id):
            messagebox.showinfo("Sucesso", "Backup excluído com sucesso")
            self._selected_backup_id = None
            self._restore_btn.configure(state="disabled")
            self._verify_btn.configure(state="disabled")
            self._delete_btn.configure(state="disabled")
            self._load_backups()
        else:
            messagebox.showerror("Erro", "Erro ao excluir backup")
    
    def _cleanup_old_backups(self):
        """Limpa backups antigos"""
        if not messagebox.askyesno(
            "Confirmar Limpeza",
            "Deseja remover backups antigos (mais de 30 dias)?\n"
            "Os 10 backups mais recentes serão mantidos."
        ):
            return
        
        removed = servico_backup.cleanup_old_backups(keep_days=30, keep_count=10)
        messagebox.showinfo("Limpeza Concluída", f"{removed} backups removidos")
        self._load_backups()
    
    def _update_progress(self, current: int, total: int, message: str):
        """Atualiza barra de progresso"""
        progress = current / total if total > 0 else 0
        self.after(0, lambda: self._progress_bar.set(progress))
        self.after(0, lambda: self._progress_label.configure(text=message))


class BackupButton(ctk.CTkButton):
    """
    Botão que abre o dialog de backup.
    
    Usage:
        btn = BackupButton(parent)
    """
    
    def __init__(self, parent, **kwargs):
        defaults = {
            "text": "💾 Backup",
            "font": font(12),
            "fg_color": THEME["primary"],
            "hover_color": THEME["primary_hover"],
            "height": 36,
            "corner_radius": RADIUS["button"],
        }
        defaults.update(kwargs)
        
        super().__init__(parent, command=self._open_dialog, **defaults)
        
        self._dialog: Optional[BackupDialog] = None
    
    def _open_dialog(self):
        self._dialog = BackupDialog(self.winfo_toplevel())
