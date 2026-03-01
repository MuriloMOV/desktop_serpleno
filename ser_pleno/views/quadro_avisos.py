# views/quadro_avisos.py
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import datetime
import html
import threading
import traceback
import logging

# Importa o serviço de mural
from services.mural import servico_mural
from services.api import api

logger = logging.getLogger('apps.desktop')

# simples escape html util
def escape_html(s):
    if s is None:
        return ""
    return html.escape(str(s))


class QuadroAvisosFrame(ctk.CTkFrame):

    def __init__(self, master, app):
        super().__init__(master, fg_color="#f3f4f6")
        self.app = app
        self.pack(fill="both", expand=True)

        # Estado
        self.posts = []  # lista de posts carregados
        self.editing_post = None  # post carregado para edição (dict)

        # modal reference (pode ser None enquanto não existe)
        self.modal = None

        # Header
        header = ctk.CTkFrame(self, fg_color="#f3f4f6")
        header.pack(fill="x", padx=40, pady=(30, 10))

        ctk.CTkLabel(
            header,
            text="Quadro de Avisos",
            font=("Inter", 26, "bold"),
            text_color="#111827"
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="+ Novo Aviso",
            fg_color="#6d28d9",
            hover_color="#5b21b6",
            text_color="white",
            corner_radius=10,
            height=36,
            width=140,
            command=self.abrir_modal
        ).pack(side="right")

        # Lista
        self.lista = ctk.CTkScrollableFrame(self, fg_color="#f3f4f6")
        self.lista.pack(fill="both", expand=True, padx=40, pady=20)

        # Construir modal (criado inicialmente, mas pode ser recriado se necessário)
        self._build_modal()

        # iniciar watcher (uma vez) para combobox/preview
        self._last_layout_val = None
        self._modal_watcher()  # roda periodicamente

        # Carregar avisos de forma assíncrona para não travar UI
        self.carregar_avisos_async()

    # ----------------------- Async helpers -----------------------
    def _run_in_thread(self, fn, callback=None, err_callback=None):
        """Executa fn() em background; quando termina chama callback(result) na main thread."""
        def _worker():
            try:
                res = fn()
                if callback:
                    self.after(0, lambda: callback(res))
            except Exception as e:
                logging = __import__('logging')
                logging.getLogger('apps.desktop').exception("Erro background")
                if err_callback:
                    self.after(0, lambda: err_callback(e))
                else:
                    # fallback: print
                    self.after(0, lambda: print("Erro background:", e, traceback.format_exc()))
        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    # ----------------------- API (async wrappers) - modo dual -----------------------
    def carregar_avisos_async(self):
        # mostra loading e dispara thread
        for w in self.lista.winfo_children():
            w.destroy()
        lbl = ctk.CTkLabel(self.lista, text="Carregando publicações...", text_color="#6b7280")
        lbl.pack(pady=12)

        def _fetch():
            # Usa o serviço mural que automaticamente decide entre API e banco local
            return servico_mural.listar_mensagens()

        def _on_result(res):
            # remove loading
            for w in self.lista.winfo_children():
                w.destroy()
            try:
                posts = []
                if isinstance(res, dict):
                    if res.get("success") is False:
                        message = res.get("message", "Erro ao carregar avisos")
                        print("Erro ao carregar avisos:", message)
                        lbl = ctk.CTkLabel(self.lista, text=f"Erro ao carregar avisos: {message}", text_color="#b91c1c")
                        lbl.pack(pady=12)
                        return
                    if "data" in res and isinstance(res["data"], list):
                        posts = res["data"]
                    elif res.get("id"):
                        posts = [res]
                elif isinstance(res, list):
                    posts = res
                
                self.posts = posts
                if not posts:
                    lbl = ctk.CTkLabel(self.lista, text="Nenhuma publicação encontrada.", text_color="#6b7280")
                    lbl.pack(pady=12)
                    return

                for post in reversed(posts):
                    if not isinstance(post, dict):
                        continue
                    self.criar_card(
                        post.get("id"),
                        post.get("titulo") or post.get("title"),
                        post.get("conteudo") or post.get("content"),
                        post.get("autor") or post.get("author") or "Sistema",
                        post.get("publicado_em") or post.get("created_at") or ""
                    )
            except Exception as e:
                print("Erro ao processar resposta do mural:", e, traceback.format_exc())
                lbl = ctk.CTkLabel(self.lista, text="Erro ao processar resposta do servidor.", text_color="#b91c1c")
                lbl.pack(pady=12)

        def _on_err(e):
            for w in self.lista.winfo_children():
                w.destroy()
            lbl = ctk.CTkLabel(self.lista, text=f"Erro ao carregar avisos: {e}", text_color="#b91c1c")
            lbl.pack(pady=12)

        self._run_in_thread(_fetch, callback=_on_result, err_callback=_on_err)

    def publicar_aviso_async(self, payload, on_success=None, on_error=None):
        def _post():
            # Usa o serviço mural que automaticamente decide entre API e banco local
            # garante publicado_em
            if not payload.get("publicado_em"):
                payload["publicado_em"] = datetime.datetime.utcnow().isoformat()
            return servico_mural.criar_mensagem(payload)

        def _cb(res):
            if isinstance(res, dict) and res.get("success") is False:
                if on_error:
                    on_error(res)
                else:
                    messagebox.showerror("Erro", f"Erro ao publicar: {res.get('message')}")
                return
            if on_success:
                on_success(res)

        def _err(e):
            if on_error:
                on_error({"success": False, "message": str(e)})
            else:
                messagebox.showerror("Erro", f"Erro ao publicar: {e}")

        self._run_in_thread(_post, callback=_cb, err_callback=_err)

    def atualizar_aviso_async(self, post_id, payload, on_success=None, on_error=None):
        def _put():
            if not payload.get("publicado_em"):
                payload["publicado_em"] = datetime.datetime.utcnow().isoformat()
            # Usa o serviço mural que automaticamente decide entre API e banco local
            return servico_mural.atualizar_mensagem(post_id, payload)

        def _cb(res):
            if isinstance(res, dict) and res.get("success") is False:
                if on_error:
                    on_error(res)
                else:
                    messagebox.showerror("Erro", f"Erro ao atualizar: {res.get('message')}")
                return
            if on_success:
                on_success(res)

        def _err(e):
            if on_error:
                on_error({"success": False, "message": str(e)})
            else:
                messagebox.showerror("Erro", f"Erro ao atualizar: {e}")

        self._run_in_thread(_put, callback=_cb, err_callback=_err)

    def deletar_aviso_async(self, post_id, on_success=None, on_error=None):
        def _del():
            # Usa o serviço mural que automaticamente decide entre API e banco local
            return servico_mural.deletar_mensagem(post_id)

        def _cb(res):
            # res pode ser dict success True ou similar
            if isinstance(res, dict) and res.get("success") is False:
                if on_error:
                    on_error(res)
                else:
                    messagebox.showerror("Erro", f"Erro ao deletar: {res.get('message')}")
                return
            if on_success:
                on_success(res)

        def _err(e):
            if on_error:
                on_error({"success": False, "message": str(e)})
            else:
                messagebox.showerror("Erro", f"Erro ao deletar: {e}")

        self._run_in_thread(_del, callback=_cb, err_callback=_err)

    # ----------------------- API (síncronos originais - mantidos por compatibilidade) -----------------------
    # (mantive os métodos síncronos caso algum outro código os use diretamente)
    def publicar_aviso(self, payload):
        if not payload.get("publicado_em"):
            payload["publicado_em"] = datetime.datetime.utcnow().isoformat()
        return servico_mural.criar_mensagem(payload)

    def atualizar_aviso(self, post_id, payload):
        if not payload.get("publicado_em"):
            payload["publicado_em"] = datetime.datetime.utcnow().isoformat()
        return servico_mural.atualizar_mensagem(post_id, payload)

    def deletar_aviso(self, post_id):
        return servico_mural.deletar_mensagem(post_id)

    # ----------------------- UI - Cards -----------------------
    def criar_card(self, aviso_id, titulo, descricao, autor, data):
        card = ctk.CTkFrame(self.lista, fg_color="white", corner_radius=12)
        card.pack(fill="x", pady=10)

        conteudo = ctk.CTkFrame(card, fg_color="white")
        conteudo.pack(fill="both", expand=True, padx=20, pady=15)

        # top area: título + botões
        top = ctk.CTkFrame(conteudo, fg_color="white")
        top.pack(fill="x")

        lbl_title = ctk.CTkLabel(top, text=escape_html(titulo or ""), font=("Inter", 18, "bold"), text_color="#111827")
        lbl_title.pack(side="left", anchor="w")

        btns = ctk.CTkFrame(top, fg_color="white")
        btns.pack(side="right")
        edit_btn = ctk.CTkButton(btns, text="Editar", width=80, height=30, fg_color="#eef2ff", text_color="#1e40af",
                                 hover_color="#dbeafe", command=lambda i=aviso_id: self._on_edit(i))
        edit_btn.pack(side="left", padx=(6, 0))
        del_btn = ctk.CTkButton(btns, text="Excluir", width=80, height=30, fg_color="#ffeef0", text_color="#b91c1c",
                                hover_color="#fee2e2", command=lambda i=aviso_id: self._on_delete(i))
        del_btn.pack(side="left", padx=(6, 0))

        # descrição
        ctk.CTkLabel(conteudo, text=escape_html(descricao or ""), wraplength=800, justify="left", text_color="#374151").pack(anchor="w", pady=(8,10))

        footer = ctk.CTkFrame(conteudo, fg_color="white")
        footer.pack(fill="x")
        ctk.CTkLabel(footer, text=f"{escape_html(autor)} • {escape_html(data)}", text_color="#6b7280", font=("Inter", 12)).pack(side="left")

    # ----------------------- Ações de editar / deletar -----------------------
    def _on_edit(self, post_id):
        def _fetch_and_open():
            # Usa o serviço mural que automaticamente decide entre API e banco local
            return servico_mural.obter_mensagem(post_id)

        def _on_res(res):
            if isinstance(res, dict) and res.get("success") is False:
                messagebox.showerror("Erro", f"Erro ao carregar publicação: {res.get('message')}")
                return
            if isinstance(res, dict) and "data" in res and isinstance(res["data"], dict):
                data = res["data"]
            else:
                data = res
            if not isinstance(data, dict):
                messagebox.showerror("Erro", "Resposta inválida do servidor ao carregar publicação.")
                return
            self._populate_modal_with_data(data)
            self.open_modal_window()

        def _on_err(e):
            messagebox.showerror("Erro", f"Erro ao carregar publicação: {e}")

        self._run_in_thread(_fetch_and_open, callback=_on_res, err_callback=_on_err)

    def _on_delete(self, post_id):
        if not messagebox.askyesno("Confirmação", "Excluir esta publicação?"):
            return

        def on_success(_):
            self.carregar_avisos_async()

        def on_error(err):
            messagebox.showerror("Erro", f"Erro ao excluir publicação: {err.get('message') if isinstance(err, dict) else err}")

        self.deletar_aviso_async(post_id, on_success=on_success, on_error=on_error)

    # ----------------------- Modal / Editor -----------------------
    def _build_modal(self):
        """Cria o toplevel modal e todos os widgets necessários; mantém oculto inicialmente.
           Se já existir um modal válido, destrói e recria (garante estado limpo)."""
        # se existir modal anterior e válido, destrói primeiro para evitar widgets pendentes
        try:
            if getattr(self, "modal", None) and self.modal.winfo_exists():
                try:
                    self.modal.grab_release()
                except Exception:
                    pass
                try:
                    self.modal.destroy()
                except Exception:
                    pass
        except Exception:
            pass

        # criar nova modal
        self.modal = ctk.CTkToplevel(self)
        self.modal.title("Publicação do Mural")
        self.modal.resizable(False, False)
        # fundo leve lilás para dar um tom sutil
        # agora usamos um tom mais neutro + borda para dar sensação de cartão elevado
        self.modal.configure(fg_color="#f7f5fb")
        # ocultar até ser usado
        self.modal.withdraw()

        # melhor posicionamento: centralizar relativamente à janela principal
        largura = 920
        altura = 700
        try:
            self.modal.geometry(f"{largura}x{altura}")
            try:
                self.modal.transient(self.master)
            except Exception:
                pass
        except Exception:
            pass

        # outer: sombra sutil simulada com borda e cor levemente mais escura
        outer = ctk.CTkFrame(self.modal, fg_color="#efe6ff", corner_radius=16, width=largura-20, height=altura-20, border_width=0)
        outer.place(relx=0.5, rely=0.5, anchor="center")

        # container: cartão branco com borda fina roxa suave
        container = ctk.CTkFrame(outer, fg_color="white", corner_radius=12, width=largura-40, height=altura-40, border_width=1, border_color="#e9ddff")
        container.place(relx=0.5, rely=0.5, anchor="center")

        # header stripe (accent)
        header_stripe = ctk.CTkFrame(container, fg_color="#f4eeff", height=60, corner_radius=10, border_width=0)
        header_stripe.place(relx=0.02, rely=0.02, relwidth=0.96)

        # Título com leve icon-like (texto estilizado) e subtitle
        ctk.CTkLabel(header_stripe, text="✦  Nova Publicação", font=("Inter", 15, "bold"), text_color="#4c1d95").place(relx=0.02, rely=0.18)
        ctk.CTkLabel(header_stripe, text="Campos à esquerda · pré-visualização à direita", font=("Inter", 11), text_color="#73619b").place(relx=0.02, rely=0.55)

        # close (x) discreto no header (mantém lógica de fechamento)
        try:
            close_btn = ctk.CTkButton(header_stripe, text="✕", width=36, height=36, fg_color="white", text_color="#6b7280",
                                      hover_color="#f3f4f6", corner_radius=10, command=self.close_modal)
            close_btn.place(relx=0.95, rely=0.12, anchor="ne")
        except Exception:
            pass

        # layout em duas colunas: esquerda form, direita preview
        left = ctk.CTkFrame(container, fg_color="transparent")
        left.place(relx=0.02, rely=0.12, relwidth=0.58, relheight=0.86)

        # Criar uma área rolável para o formulário (assim o footer fica fixo)
        form_scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        form_scroll.pack(side="top", fill="both", expand=True, padx=8, pady=8)

        # frm agora refere-se ao scrollable frame (onde os campos são empacotados)
        frm = form_scroll

        right = ctk.CTkFrame(container, fg_color="transparent")
        right.place(relx=0.62, rely=0.12, relwidth=0.36, relheight=0.86)

        # FORMULÁRIO (frm) - espaçamentos mais generosos e tipografia ajustada
        # Título
        ctk.CTkLabel(frm, text="Título", font=("Inter", 13, "bold"), text_color="#33323d").pack(anchor="w", pady=(10,4))
        self.f_titulo = ctk.CTkEntry(frm, placeholder_text="Digite o título", height=44, corner_radius=10, fg_color="#fbfbff", border_width=1, border_color="#efe6ff")
        self.f_titulo.pack(fill="x", pady=(0,12))

        # Conteúdo (textarea)
        ctk.CTkLabel(frm, text="Conteúdo", font=("Inter", 13, "bold"), text_color="#33323d").pack(anchor="w", pady=(2,4))
        self.f_conteudo = ctk.CTkTextbox(frm, height=150, corner_radius=10, fg_color="#fbfbff", border_width=1, border_color="#efe6ff")
        self.f_conteudo.pack(fill="x", pady=(0,12))

        # Categoria / Autor
        row = ctk.CTkFrame(frm, fg_color="transparent")
        row.pack(fill="x", pady=(6,8))
        ctk.CTkLabel(row, text="Categoria", font=("Inter", 12), text_color="#33323d").pack(side="left", padx=(0,8))
        self.f_categoria = ctk.CTkComboBox(row, values=["informativo","aviso","aula","urgente","evento"], width=180, button_color="#efe6ff", fg_color="white", dropdown_fg_color="white")
        self.f_categoria.set("informativo")
        self.f_categoria.pack(side="left")
        ctk.CTkLabel(row, text="Autor", font=("Inter", 12), text_color="#33323d").pack(side="left", padx=(12,8))
        self.f_autor = ctk.CTkEntry(row, placeholder_text="Nome do autor", width=160, height=36, corner_radius=8, fg_color="#fbfbff", border_width=1, border_color="#efe6ff")
        self.f_autor.pack(side="left")

        # local fisico / link externo
        row2 = ctk.CTkFrame(frm, fg_color="transparent")
        row2.pack(fill="x", pady=(8,8))
        ctk.CTkLabel(row2, text="Local Físico", font=("Inter", 12), text_color="#33323d").pack(side="left", padx=(0,8))
        self.f_local = ctk.CTkEntry(row2, placeholder_text="Ex: Auditório", width=220, height=36, corner_radius=8, fg_color="#fbfbff", border_width=1, border_color="#efe6ff")
        self.f_local.pack(side="left")
        ctk.CTkLabel(row2, text="Link Externo", font=("Inter", 12), text_color="#33323d").pack(side="left", padx=(12,8))
        self.f_link = ctk.CTkEntry(row2, placeholder_text="https://...", width=200, height=36, corner_radius=8, fg_color="#fbfbff", border_width=1, border_color="#efe6ff")
        self.f_link.pack(side="left")

        # data agendamento / horario evento
        row3 = ctk.CTkFrame(frm, fg_color="transparent")
        row3.pack(fill="x", pady=(8,8))
        ctk.CTkLabel(row3, text="Data Agendamento (YYYY-MM-DD)", font=("Inter", 11), text_color="#33323d").pack(side="left", padx=(0,8))
        self.f_data_ag = ctk.CTkEntry(row3, placeholder_text="YYYY-MM-DD", width=150, height=36, corner_radius=8, fg_color="#fbfbff", border_width=1, border_color="#efe6ff")
        self.f_data_ag.pack(side="left")
        ctk.CTkLabel(row3, text="Horário Evento (YYYY-MM-DD HH:MM)", font=("Inter", 11), text_color="#33323d").pack(side="left", padx=(12,8))
        self.f_horario_evento = ctk.CTkEntry(row3, placeholder_text="YYYY-MM-DD HH:MM", width=190, height=36, corner_radius=8, fg_color="#fbfbff", border_width=1, border_color="#efe6ff")
        self.f_horario_evento.pack(side="left")

        # layout select
        ctk.CTkLabel(frm, text="Layout", font=("Inter", 12, "bold"), text_color="#33323d").pack(anchor="w", pady=(10,4))
        self.f_layout = ctk.CTkComboBox(frm, values=["single","grid-2","grid-3","grid-4"], width=220, button_color="#efe6ff", fg_color="white", dropdown_fg_color="white")
        self.f_layout.set("single")
        self.f_layout.pack(anchor="w", pady=(0,8))

        # blocos editor container (dinâmico)
        ctk.CTkLabel(frm, text="Blocos (apenas para layouts grid-*):", font=("Inter", 12), text_color="#33323d").pack(anchor="w", pady=(6,4))
        self.blocos_container = ctk.CTkFrame(frm, fg_color="#fbfbff", corner_radius=8, border_width=1, border_color="#efe6ff")
        self.blocos_container.pack(fill="both", expand=False, pady=(0,8), padx=(0,4))

        # botões de reorder e helpers
        helper_row = ctk.CTkFrame(frm, fg_color="transparent")
        helper_row.pack(fill="x", pady=(6,10))
        ctk.CTkButton(helper_row, text="Adicionar Bloco (manual)", width=170, corner_radius=8, fg_color="#6d28d9", hover_color="#5b21b6", text_color="white", command=self._manual_add_block).pack(side="left", padx=(0,8))
        ctk.CTkButton(helper_row, text="Reset Blocos", width=120, corner_radius=8, fg_color="white", text_color="#6b7280", command=lambda: self._render_block_editors('single', [])).pack(side="left", padx=(6,0))

        # save / cancel - footer fixo fora da área rolável
        footer = ctk.CTkFrame(left, fg_color="transparent", height=64)
        footer.pack(side="bottom", fill="x", pady=(6,8))
        try:
            footer.pack_propagate(False)
        except Exception:
            pass

        self._cancel_btn = ctk.CTkButton(footer, text="Cancelar", fg_color="white", text_color="#4b4b57", width=140, corner_radius=8, command=self.close_modal)
        self._cancel_btn.pack(side="left", padx=(12,6), pady=12)
        self._publish_btn = ctk.CTkButton(footer, text="Publicar", fg_color="#7c3aed", text_color="white", width=140, corner_radius=8, command=self._publish_from_modal)
        self._publish_btn.pack(side="right", padx=(12,6), pady=12)

        # Preview (right) - cartão com borda roxa sutil e fundo levemente tons de branco
        preview_label = ctk.CTkLabel(right, text="Pré-visualização", font=("Inter", 14, "bold"), text_color="#111827")
        preview_label.pack(anchor="nw", pady=(6,6), padx=6)
        self.preview_area = ctk.CTkFrame(right, fg_color="#ffffff", corner_radius=10, border_width=1, border_color="#efe6ff")
        self.preview_area.pack(fill="both", expand=True, padx=8, pady=6)

        # inside preview: title, icon, content, blocks area, footer info
        self.prev_title = ctk.CTkLabel(self.preview_area, text="Título da Publicação", font=("Inter", 16, "bold"), text_color="#111827")
        self.prev_title.pack(anchor="nw", pady=(14,6), padx=14)
        self.prev_author = ctk.CTkLabel(self.preview_area, text="Analista SerPleno", font=("Inter", 11), text_color="#6b7280")
        self.prev_author.pack(anchor="nw", padx=14)
        self.prev_content = ctk.CTkLabel(self.preview_area, text="O conteúdo aparecerá aqui enquanto você digita...", wraplength=300, justify="left", text_color="#374151")
        self.prev_content.pack(anchor="nw", pady=(10,8), padx=14)
        self.prev_blocks_wrap = ctk.CTkFrame(self.preview_area, fg_color="transparent")
        self.prev_blocks_wrap.pack(fill="x", padx=14, pady=(6,12))

        # Bind inputs to update preview
        for widget in [self.f_titulo, self.f_conteudo, self.f_categoria, self.f_autor, self.f_local, self.f_link, self.f_data_ag, self.f_horario_evento, self.f_layout]:
            try:
                widget.bind("<KeyRelease>", lambda e: self._update_preview())
            except Exception:
                try:
                    widget.bind("<<ComboboxSelected>>", lambda e: self._update_preview())
                except Exception:
                    pass

        # internal state for block editors: list of dicts {frame, title_entry, content_text, icon_combo}
        self._block_editors = []

    def open_modal_window(self):
        # assegura que modal existe e foi construída
        if not getattr(self, "modal", None) or not self.modal.winfo_exists():
            self._build_modal()

        self.modal.deiconify()
        self.modal.lift()
        # agora sim pedimos grab para modal ao abrir
        try:
            self.modal.grab_set()
        except Exception:
            pass
        self._update_preview()

    def close_modal(self):
        try:
            if getattr(self, "modal", None) and self.modal.winfo_exists():
                try:
                    self.modal.grab_release()
                except Exception:
                    pass
                try:
                    self.modal.destroy()
                except Exception:
                    pass
        except Exception:
            pass
        # garantir referência limpa
        self.modal = None
        # clear editing post
        self.editing_post = None

    def abrir_modal(self):
        """Abre modal novo (reseta campos). Garante reconstrução caso widgets anteriores estejam inválidos."""
        # se modal inexistente ou inválida, cria novamente
        if not getattr(self, "modal", None) or not self.modal.winfo_exists():
            self._build_modal()

        # agora resetar campos (se algum widget ainda for inválido, recriamos novamente)
        try:
            # título
            self.f_titulo.delete(0, "end")
            # conteudo
            self.f_conteudo.delete("1.0", "end")
            # outros fields
            self.f_categoria.set("informativo")
            self.f_autor.delete(0, "end")
            self.f_local.delete(0, "end")
            self.f_link.delete(0, "end")
            self.f_data_ag.delete(0, "end")
            self.f_horario_evento.delete(0, "end")
            self.f_layout.set("single")
            self._render_block_editors("single", [])
            self._update_preview()
            # abrir
            self.open_modal_window()
        except Exception:
            # se qualquer widget estiver em estado inválido, recriar modal e tentar novamente uma vez
            try:
                self._build_modal()
                self.f_titulo.delete(0, "end")
                self.f_conteudo.delete("1.0", "end")
                self.f_categoria.set("informativo")
                self.f_autor.delete(0, "end")
                self.f_local.delete(0, "end")
                self.f_link.delete(0, "end")
                self.f_data_ag.delete(0, "end")
                self.f_horario_evento.delete(0, "end")
                self.f_layout.set("single")
                self._render_block_editors("single", [])
                self._update_preview()
                self.open_modal_window()
            except Exception as e:
                # fallback: informar erro
                messagebox.showerror("Erro", f"Não foi possível abrir modal: {e}")

    def _modal_watcher(self):
        """Watcher para combobox layout e preview updates periódicos (CTk combobox não tem trace fácil)"""
        try:
            if getattr(self, "modal", None) and self.modal.winfo_exists():
                try:
                    cur = self.f_layout.get()
                    if cur != self._last_layout_val:
                        self._last_layout_val = cur
                        existing = []
                        if self.editing_post and isinstance(self.editing_post.get("blocos"), list):
                            existing = self.editing_post.get("blocos")
                        self._render_block_editors(cur, existing)
                        self._update_preview()
                except Exception:
                    pass
        except Exception:
            pass
        # sempre agendar próxima verificação
        self.after(300, self._modal_watcher)

    def _render_block_editors(self, layout, existing):
        for w in self.blocos_container.winfo_children():
            w.destroy()
        self._block_editors = []
        cols = 1
        if layout and layout.startswith("grid-"):
            try:
                cols = int(layout.split("-")[1])
            except Exception:
                cols = 1
        if cols <= 1:
            return
        for i in range(cols):
            ex = existing[i] if existing and i < len(existing) else {}
            frame = ctk.CTkFrame(self.blocos_container, fg_color="white", corner_radius=8, border_width=1, border_color="#efe6ff")
            frame.pack(fill="x", pady=6, padx=6)
            lab_t = ctk.CTkLabel(frame, text=f"Bloco #{i+1} - Título", font=("Inter", 11), text_color="#374151")
            lab_t.pack(anchor="w", pady=(6,0), padx=8)
            entry_t = ctk.CTkEntry(frame, placeholder_text="Título do bloco", height=34, corner_radius=6, fg_color="#fbfbff", border_width=1, border_color="#efe6ff")
            entry_t.pack(fill="x", padx=8, pady=(0,6))
            entry_t.delete(0, "end"); entry_t.insert(0, ex.get("titulo","") if ex else "")

            lab_c = ctk.CTkLabel(frame, text="Conteúdo do Bloco", font=("Inter", 11), text_color="#374151")
            lab_c.pack(anchor="w", padx=8)
            txt = ctk.CTkTextbox(frame, height=80, corner_radius=6, fg_color="#fbfbff", border_width=1, border_color="#efe6ff")
            txt.pack(fill="x", padx=8, pady=(0,6))
            txt.delete("1.0", "end"); txt.insert("1.0", ex.get("conteudo","") if ex else "")

            lab_icon = ctk.CTkLabel(frame, text="Ícone (nome Lucide)", font=("Inter", 11), text_color="#374151")
            lab_icon.pack(anchor="w", padx=8)
            comb = ctk.CTkComboBox(frame, values=["","phone","mail","clock","calendar","help-circle","user","users","alert-triangle","info","check","x","external-link","link"], width=220)
            comb.pack(anchor="w", padx=8, pady=(4,8))
            comb.set(ex.get("icon","") if ex else "")

            # reorder buttons (up / down)
            op_row = ctk.CTkFrame(frame, fg_color="transparent")
            op_row.pack(fill="x", padx=8, pady=(0,8))
            upb = ctk.CTkButton(op_row, text="↑", width=40, height=28, command=lambda f=frame: self._move_block_up(f))
            upb.pack(side="left", padx=(0,6))
            downb = ctk.CTkButton(op_row, text="↓", width=40, height=28, command=lambda f=frame: self._move_block_down(f))
            downb.pack(side="left")
            delb = ctk.CTkButton(op_row, text="Remover", width=100, fg_color="#fee2e2", text_color="#b91c1c", command=lambda f=frame: self._remove_block(f))
            delb.pack(side="right")

            self._block_editors.append({
                "frame": frame,
                "title": entry_t,
                "content": txt,
                "icon": comb
            })

    def _manual_add_block(self):
        cur_layout = self.f_layout.get()
        if not cur_layout or cur_layout == "single":
            self.f_layout.set("grid-2")
            cur_layout = "grid-2"
        cols = int(cur_layout.split("-")[1])
        existing = []
        for be in self._block_editors:
            existing.append({
                "titulo": be["title"].get(),
                "conteudo": be["content"].get("1.0","end").strip(),
                "icon": be["icon"].get()
            })
        existing.append({"titulo": "", "conteudo": "", "icon": ""})
        self._render_block_editors(cur_layout, existing)
        self._update_preview()

    def _move_block_up(self, frame):
        parent = self.blocos_container
        children = list(parent.children.values())
        if frame not in children:
            return
        idx = children.index(frame)
        if idx > 0:
            frame.pack_forget()
            frame.pack(before=children[idx-1])
            self._reindex_block_editors()
            self._update_preview()

    def _move_block_down(self, frame):
        parent = self.blocos_container
        children = list(parent.children.values())
        if frame not in children:
            return
        idx = children.index(frame)
        if idx < len(children)-1:
            frame.pack_forget()
            next_widget = children[idx+1]
            next_widget.pack_forget()
            next_widget.pack()
            frame.pack()
            self._reindex_block_editors()
            self._update_preview()

    def _remove_block(self, frame):
        frame.destroy()
        self._reindex_block_editors()
        self._update_preview()

    def _reindex_block_editors(self):
        new_editors = []
        kids = [w for w in self.blocos_container.winfo_children()]
        for f in kids:
            title = None; content = None; icon = None
            for child in f.winfo_children():
                if isinstance(child, ctk.CTkEntry) and title is None:
                    title = child
                if isinstance(child, ctk.CTkTextbox) and content is None:
                    content = child
                if isinstance(child, ctk.CTkComboBox) and icon is None:
                    icon = child
            if title and content and icon:
                new_editors.append({"frame": f, "title": title, "content": content, "icon": icon})
        self._block_editors = new_editors

    def _collect_blocks_payload(self):
        arr = []
        for be in self._block_editors:
            titulo = be["title"].get().strip()
            conteudo = be["content"].get("1.0", "end").strip()
            icon = be["icon"].get() if hasattr(be["icon"], "get") else ""
            if titulo or conteudo or icon:
                arr.append({"titulo": titulo, "conteudo": conteudo, "icon": icon})
        return arr

    def _populate_modal_with_data(self, data):
        # garante modal válida antes de popular
        if not getattr(self, "modal", None) or not self.modal.winfo_exists():
            self._build_modal()

        self.editing_post = data
        self.f_titulo.delete(0, "end"); self.f_titulo.insert(0, data.get("titulo") or data.get("title","") or "")
        self.f_conteudo.delete("1.0","end"); self.f_conteudo.insert("1.0", data.get("conteudo") or data.get("content","") or "")
        cat = data.get("categoria") or data.get("category") or "informativo"
        self.f_categoria.set(cat)
        self.f_autor.delete(0,"end"); self.f_autor.insert(0, data.get("autor") or data.get("author","") or "")
        self.f_local.delete(0,"end"); self.f_local.insert(0, data.get("local_fisico","") or "")
        self.f_link.delete(0,"end"); self.f_link.insert(0, data.get("link_externo","") or "")
        dag = data.get("data_agendamento") or ""
        if dag:
            try:
                d = dag.split("T")[0]
                self.f_data_ag.delete(0,"end"); self.f_data_ag.insert(0, d)
            except Exception:
                self.f_data_ag.delete(0,"end"); self.f_data_ag.insert(0, dag)
        else:
            self.f_data_ag.delete(0,"end")
        he = data.get("horario_evento") or ""
        if he:
            try:
                dt = he.replace("T", " ").split("+")[0].split("Z")[0]
                dt = dt[:16]
                self.f_horario_evento.delete(0,"end"); self.f_horario_evento.insert(0, dt)
            except Exception:
                self.f_horario_evento.delete(0,"end"); self.f_horario_evento.insert(0, he)
        else:
            self.f_horario_evento.delete(0,"end")
        layout = data.get("layout") or "single"
        self.f_layout.set(layout)
        blocos = data.get("blocos") or []
        self._render_block_editors(layout, blocos)
        self._update_preview()

    def _update_preview(self):
        # Se modal não existe, nada a atualizar
        if not getattr(self, "modal", None) or not self.modal.winfo_exists():
            return

        title = self.f_titulo.get().strip() or "Título da Publicação"
        author = self.f_autor.get().strip() or "Analista SerPleno"
        content = self.f_conteudo.get("1.0", "end").strip() or "O conteúdo aparecerá aqui enquanto você digita..."
        self.prev_title.configure(text=title)
        self.prev_author.configure(text=author)
        layout = self.f_layout.get() or "single"
        if layout == "single":
            self.prev_content.configure(text=content)
            for w in self.prev_blocks_wrap.winfo_children():
                w.destroy()
        else:
            self.prev_content.configure(text="")
            for w in self.prev_blocks_wrap.winfo_children():
                w.destroy()
            cols = 1
            try:
                cols = int(layout.split("-")[1])
            except Exception:
                cols = 1
            blocks = self._collect_blocks_payload()
            n = min(cols, 4)
            # use container tkinter frame dentro do prev_blocks_wrap (CTk não tem grid interno robusto para este caso)
            wrap = tk.Frame(self.prev_blocks_wrap, bg="#ffffff")
            wrap.pack(fill="both", padx=2)
            for i in range(n):
                b = blocks[i] if i < len(blocks) else {"titulo":"", "conteudo":""}
                # cada bloco com borda e padding para visual mais limpo
                frame = tk.Frame(wrap, bg="#ffffff", bd=1, relief="flat", highlightthickness=1, highlightbackground="#f0ebff")
                frame.grid(row=0, column=i, padx=6, pady=6, sticky="n")
                lbl_t = tk.Label(frame, text=b.get("titulo",""), font=("Inter", 10, "bold"), bg="#ffffff", anchor="w")
                lbl_t.pack(fill="x", padx=10, pady=(8,2))
                lbl_c = tk.Label(frame, text=b.get("conteudo","").replace("\n","\n"), font=("Inter", 9), bg="#ffffff", fg="#374151", justify="left", wraplength=200)
                lbl_c.pack(fill="both", padx=10, pady=(0,10))
            for i in range(n):
                wrap.grid_columnconfigure(i, weight=1)

    def _collect_payload_from_form(self):
        payload = {
            "titulo": self.f_titulo.get().strip(),
            "conteudo": self.f_conteudo.get("1.0","end").strip(),
            "categoria": self.f_categoria.get() or "informativo",
            "autor": self.f_autor.get().strip() or None,
            "local_fisico": self.f_local.get().strip() or None,
            "link_externo": self.f_link.get().strip() or None,
            "data_agendamento": self.f_data_ag.get().strip() or None,
            "horario_evento": None,
            "layout": self.f_layout.get() or "single",
            "blocos": [],
            "ativo": True
        }
        he = self.f_horario_evento.get().strip()
        if he:
            try:
                dt = datetime.datetime.strptime(he, "%Y-%m-%d %H:%M")
                payload["horario_evento"] = dt.isoformat()
            except Exception:
                payload["horario_evento"] = he
        payload["blocos"] = self._collect_blocks_payload()
        if self.editing_post and isinstance(self.editing_post.get("publicado_em"), str):
            payload["publicado_em"] = self.editing_post.get("publicado_em")
        else:
            payload["publicado_em"] = datetime.datetime.utcnow().isoformat()
        return payload

    def _on_modal_save(self):
        payload = self._collect_payload_from_form()
        if not payload["titulo"] or (payload["layout"] == "single" and (not payload["conteudo"])):
            messagebox.showwarning("Atenção", "Preencha título e conteúdo (ou adicione blocos para layout grid).")
            return

        # desativa botões enquanto salva
        try:
            self._publish_btn.configure(state="disabled")
            self._cancel_btn.configure(state="disabled")
        except Exception:
            pass

        def on_success(res):
            try:
                # re-enable
                self._publish_btn.configure(state="normal")
                self._cancel_btn.configure(state="normal")
            except Exception:
                pass
            # fechar modal e recarregar
            self.close_modal()
            self.carregar_avisos_async()

        def on_error(err):
            try:
                self._publish_btn.configure(state="normal")
                self._cancel_btn.configure(state="normal")
            except Exception:
                pass
            messagebox.showerror("Erro ao salvar publicação", f"{err.get('message') if isinstance(err, dict) else err}")

        if self.editing_post and self.editing_post.get("id"):
            post_id = self.editing_post.get("id")
            self.atualizar_aviso_async(post_id, payload, on_success=on_success, on_error=on_error)
        else:
            self.publicar_aviso_async(payload, on_success=on_success, on_error=on_error)

    # ----------------------- Small modal-level wrapper that triggers the posting logic
    # keeps UI wiring clean and ensures the publish button is explicitly tied to modal actions
    def _publish_from_modal(self):
        """
        Wrapper invoked by the modal's Publish button.
        This simply calls the main modal-save logic (which builds payload,
        handles validation, disables buttons, and calls the async poster).
        Kept separated so the button command remains concise and the modal
        control flow is obvious.
        """
        try:
            self._on_modal_save()
        except Exception as e:
            # unexpected errors surfaced to user
            messagebox.showerror("Erro", f"Erro ao tentar publicar: {e}")
