import customtkinter as ctk
from services.mural import ServicoMural
# Compat alias para testes
BoardService = ServicoMural
import threading
from datetime import datetime
import webbrowser
import os

from ui_theme import THEME, SPACING, RADIUS, font

class QuadroAvisosFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_mural = ServicoMural()

        self.colors = THEME

        # Configuração do layout principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ----- HEADER -----
        self.criar_header()

        # ----- CONTEÚDO PRINCIPAL -----
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(10, 24))
        self.main_container.grid_columnconfigure(0, weight=3) # Feed
        self.main_container.grid_columnconfigure(1, weight=1) # Sidebar (Categorias/Fixados)

        # 1. Feed de Avisos
        self.criar_feed()
        
        # 2. Sidebar Lateral
        self.criar_sidebar()
        
        self.load_messages()

    def criar_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 8))
        
        ctk.CTkLabel(
            header,
            text="Quadro de Avisos",
            font=font(24, "bold"),
            text_color=self.colors["text"]
        ).pack(side="left")

        # Botão Novo Aviso
        ctk.CTkButton(
            header,
            text="+ Novo Comunicado", 
            fg_color=self.colors["primary"],
            hover_color="#4F46E5",
            text_color="white",
            font=font(14, "bold"),
            height=40,
            corner_radius=RADIUS["button"],
            command=self.novo_aviso
        ).pack(side="right")

    def criar_feed(self):
        self.scroll_avisos = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        self.scroll_avisos.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        
        # Title Section
        ctk.CTkLabel(self.scroll_avisos, text="Últimas Atualizações", font=font(16, "bold"), text_color=self.colors["text"]).pack(anchor="w", pady=(0, 15))

    def criar_sidebar(self):
        sidebar = ctk.CTkFrame(self.main_container, fg_color="transparent")
        sidebar.grid(row=0, column=1, sticky="nsew")
        
        # Card Fixados
        card_fix = ctk.CTkFrame(sidebar, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        card_fix.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(card_fix, text="📌 Importante", font=font(14, "bold"), text_color=self.colors["text"]).pack(anchor="w", padx=15, pady=15)
        
        self.criar_item_fixado(card_fix, "Prazo de Rematrícula", "Até 15/06")
        self.criar_item_fixado(card_fix, "Manutenção no Sistema", "Domingo, 02:00h")

    def criar_item_fixado(self, parent, titulo, info):
        item = ctk.CTkFrame(parent, fg_color="transparent")
        item.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(item, text=titulo, font=font(13, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        ctk.CTkLabel(item, text=info, font=font(12), text_color=self.colors["text_muted"]).pack(anchor="w")

    def load_messages(self):
        def fetch():
            res = self.servico_mural.listar_mensagens()
            self.after(0, lambda: self.render_messages(res))
        threading.Thread(target=fetch, daemon=True).start()

    def render_messages(self, result):
        # Clear feed content skipping the title
        for w in self.scroll_avisos.winfo_children():
            if isinstance(w, ctk.CTkFrame) and getattr(w, "is_message_card", False):
                w.destroy()
            
        items = []
        if result.get('success'):
            data = result.get('data', [])
            if isinstance(data, list): items = data
            elif isinstance(data, dict): items = data.get('results', [])

        if not items:
            # Mock Items if empty
            items = [
                {"title": "Reunião Pedagógica Semanal", "content": "A reunião ocorrerá na sala 302 às 14h. Pauta: Alinhamento de final de semestre e conselho de classe.", "author": "Coordenação", "date": "10/05/2024", "tag": "Pedagógico"},
                {"title": "Atualização do Sistema", "content": "O sistema passará por instabilidade no dia 12/05 devido à migração de servidores.", "author": "TI Suporte", "date": "09/05/2024", "tag": "Infraestrutura"},
            ]

        for item in items:
            self.criar_card_aviso(item)

    def criar_card_aviso(self, item):
        card = ctk.CTkFrame(self.scroll_avisos, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        card.pack(fill="x", pady=10)
        card.is_message_card = True # Marker

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=20)

        # Header: Tag + Date
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        
        tag = item.get('tag') or item.get('category', 'Geral')
        tag_lbl = ctk.CTkLabel(
            header, text=f" {tag} ", fg_color=self.colors["tag_bg"], text_color=self.colors["tag_text"], 
            corner_radius=6, font=font(11, "bold"), height=24
        )
        tag_lbl.pack(side="left")
        
        date = item.get("date") or item.get("created_at") or "Hoje"
        ctk.CTkLabel(header, text=date, font=font(12), text_color=self.colors["text_muted"]).pack(side="right")

        # Title & Content
        ctk.CTkLabel(inner, text=item.get("title", "Sem título"), font=font(16, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        ctk.CTkLabel(inner, text=item.get("content", ""), font=font(14), text_color=self.colors["text_muted"], wraplength=600, justify="left").pack(anchor="w", pady=(5, 10))

        # Footer: Author
        author = item.get("author", "Sistema")
        footer = ctk.CTkFrame(inner, fg_color="transparent")
        footer.pack(fill="x", pady=(5, 0))
        
        ctk.CTkLabel(footer, text="👤", font=font(14)).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(footer, text=author, font=font(12, "bold"), text_color=self.colors["text"]).pack(side="left")

        # Attachments (if any)
        attachments = item.get('attachments') or []
        if attachments:
            attach_frm = ctk.CTkFrame(inner, fg_color="transparent")
            attach_frm.pack(fill="x", pady=(8, 0))
            ctk.CTkLabel(attach_frm, text="📎 Anexos:", font=font(12, "bold"), text_color=self.colors["text"]).pack(side="left")
            for att in attachments:
                name = att.get('name') or att.get('filename') or att.get('url')
                url = att.get('url')

                def open_in_browser(u=url):
                    try:
                        webbrowser.open(u)
                    except Exception:
                        print('Erro ao abrir anexo:', u)

                def baixar_arquivo(u=url, fname=name):
                    from tkinter import filedialog, messagebox
                    import time
                    # Save dialog
                    try:
                        path = filedialog.asksaveasfilename(initialfile=fname, title='Salvar anexo como')
                        if not path:
                            return

                        # Progress modal
                        progress_win = ctk.CTkToplevel(self)
                        progress_win.title('Download')
                        progress_win.geometry('420x140')
                        lbl = ctk.CTkLabel(progress_win, text=f'Download: {fname}', anchor='w')
                        lbl.pack(fill='x', padx=12, pady=(12, 6))
                        # expose label for tests
                        progress_win.info_lbl = None
                        prog = ctk.CTkProgressBar(progress_win)
                        prog.set(0)
                        prog.pack(fill='x', padx=12, pady=(6, 6))

                        info_lbl = ctk.CTkLabel(progress_win, text='0 KB/s • ETA: --:--', anchor='w')
                        info_lbl.pack(fill='x', padx=12, pady=(0, 6))
                        # attach to window so tests can access
                        progress_win.info_lbl = info_lbl

                        btn_cancel = ctk.CTkButton(progress_win, text='Cancelar', width=100)
                        btn_cancel.pack(pady=(0, 12))

                        cancel_event = threading.Event()

                        def do_download():
                            try:
                                import requests as _requests
                                r = _requests.get(u, stream=True)
                                r.raise_for_status()
                                total = r.headers.get('content-length')
                                if total:
                                    total = int(total)
                                downloaded = 0
                                start_time = None

                                with open(path, 'wb') as f:
                                    for chunk in r.iter_content(8192):
                                        if cancel_event.is_set():
                                            # remove incomplete file
                                            try:
                                                f.close()
                                                os.remove(path)
                                            except Exception:
                                                pass
                                            try:
                                                progress_win.destroy()
                                            except Exception:
                                                pass
                                            return
                                        if chunk:
                                            if start_time is None:
                                                start_time = __import__('time').time()
                                            f.write(chunk)
                                            downloaded += len(chunk)

                                            # update progress
                                            if total:
                                                pct = downloaded / total
                                                self.after(0, lambda p=pct: prog.set(p))

                                            # compute speed and eta
                                            elapsed = __import__('time').time() - start_time if start_time else 0.0001
                                            speed_bps = downloaded / max(elapsed, 1e-6)
                                            speed_text = self._format_speed(speed_bps)
                                            eta_text = '--:--'
                                            if total and speed_bps > 0:
                                                remaining = total - downloaded
                                                eta = int(remaining / speed_bps)
                                                eta_min = eta // 60
                                                eta_sec = eta % 60
                                                eta_text = f"{eta_min:02d}:{eta_sec:02d}"

                                            info_str = f"{speed_text} • ETA: {eta_text}"
                                            self.after(0, lambda s=info_str: info_lbl.configure(text=s))

                                try:
                                    self.after(0, lambda: prog.set(1.0))
                                    try:
                                        messagebox.showinfo('Download concluído', f'Arquivo salvo em {path}')
                                    except Exception:
                                        pass
                                finally:
                                    try:
                                        progress_win.destroy()
                                    except Exception:
                                        pass
                            except Exception as e:
                                try:
                                    messagebox.showerror('Erro', f'Falha ao baixar: {e}')
                                except Exception:
                                    print('Erro ao baixar anexo:', e)
                                try:
                                    progress_win.destroy()
                                except Exception:
                                    pass

                        th = threading.Thread(target=do_download, daemon=True)
                        th.start()

                        def cancel():
                            cancel_event.set()
                            try:
                                btn_cancel.configure(state='disabled')
                            except Exception:
                                pass

                        btn_cancel.configure(command=cancel)

                        # attach helpers for tests
                        return {'thread': th, 'cancel_event': cancel_event, 'progress_win': progress_win}

                    except Exception as e:
                        try:
                            messagebox.showerror('Erro', f'Falha ao baixar: {e}')
                        except Exception:
                            print('Erro ao baixar anexo:', e)

                def preview_attachment(u=url, fname=name):
                    """Preview images or attempt to render PDF first page if possible."""
                    lower = (fname or '').lower() if fname else (u or '').lower()
                    if lower.endswith('.pdf'):
                        # try PyMuPDF (fitz)
                        try:
                            import fitz
                            import requests as _requests
                            from io import BytesIO
                            r = _requests.get(u)
                            r.raise_for_status()
                            doc = fitz.open(stream=r.content, filetype='pdf')
                            page = doc.load_page(0)
                            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                            img_bytes = pix.tobytes('png')

                            from PIL import Image, ImageTk
                            from io import BytesIO as _BytesIO
                            img = Image.open(_BytesIO(img_bytes))
                            img.thumbnail((900, 700))
                            photo = ImageTk.PhotoImage(img)

                            top = ctk.CTkToplevel(self)
                            top.title(f'Preview - {fname}')
                            lbl = ctk.CTkLabel(top, image=photo)
                            lbl.image = photo
                            lbl.pack(fill='both', expand=True)
                            return
                        except Exception:
                            try:
                                webbrowser.open(u)
                            except Exception as e:
                                print('Preview não disponível:', e)
                            return
                    # otherwise try image preview
                    try:
                        import requests as _requests
                        from io import BytesIO
                        from PIL import Image, ImageTk

                        r = _requests.get(u)
                        r.raise_for_status()
                        img = Image.open(BytesIO(r.content))
                        img.thumbnail((900, 700))
                        photo = ImageTk.PhotoImage(img)

                        top = ctk.CTkToplevel(self)
                        top.title(f'Preview - {fname}')
                        lbl = ctk.CTkLabel(top, image=photo)
                        lbl.image = photo
                        lbl.pack(fill='both', expand=True)
                    except Exception:
                        # fallback: open in browser
                        try:
                            webbrowser.open(u)
                        except Exception as e:
                            print('Preview não disponível:', e)

                btn = ctk.CTkButton(attach_frm, text=name, height=28, width=120, command=open_in_browser, fg_color=self.colors["bg_alt"], text_color=self.colors["text"]) 
                # Expose helpers for tests and advanced actions
                def start_download(u=url, n=name):
                    res = baixar_arquivo(u, n)
                    # store control handles
                    if isinstance(res, dict):
                        btn._download_thread = res.get('thread')
                        btn._cancel_event = res.get('cancel_event')
                        btn._progress_win = res.get('progress_win')
                        btn._info_lbl = getattr(res.get('progress_win'), 'info_lbl', None)
                        return res
                btn.download = start_download
                def cancel_download():
                    try:
                        if getattr(btn, '_cancel_event', None):
                            btn._cancel_event.set()
                    except Exception:
                        pass
                btn.cancel_download = cancel_download
                btn.preview = lambda u=url, n=name: preview_attachment(u, n)
                btn.pack(side="left", padx=(8, 0))
    def criar_aviso(self, dados):
        """Wrapper to call the service and reload the messages. Returns True if created."""
        try:
            res = self.servico_mural.criar_mensagem(dados)
            if res.get('success'):
                try:
                    import tkinter.messagebox as mb
                    mb.showinfo('Sucesso', res.get('message', 'Aviso criado com sucesso'))
                except Exception:
                    pass
                self.load_messages()
                return True
            else:
                try:
                    import tkinter.messagebox as mb
                    mb.showerror('Erro', res.get('message', 'Erro ao criar aviso'))
                except Exception:
                    pass
        except Exception as e:
            print('Erro ao criar aviso:', e)
        return False

    def _format_speed(self, bps: float) -> str:
        """Format bytes-per-second into human readable string (KB/s, MB/s)."""
        if bps <= 0:
            return '0 KB/s'
        kb = bps / 1024.0
        if kb < 1024:
            return f"{kb:.1f} KB/s"
        mb = kb / 1024.0
        return f"{mb:.2f} MB/s"

    def novo_aviso(self):
        import tkinter as tk
        from tkinter import messagebox, filedialog

        modal = ctk.CTkToplevel(self)
        modal.title("Novo Comunicado")
        modal.geometry("640x420")
        modal.transient(self)
        modal.grab_set()

        frm = ctk.CTkFrame(modal, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frm, text="Título", font=font(11, "bold")).pack(anchor="w")
        entry_title = ctk.CTkEntry(frm, width=580)
        entry_title.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(frm, text="Categoria / Tag", font=font(11, "bold")).pack(anchor="w")
        entry_tag = ctk.CTkEntry(frm, width=300)
        entry_tag.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(frm, text="Conteúdo", font=font(11, "bold")).pack(anchor="w")
        txt_content = ctk.CTkTextbox(frm, height=180, fg_color=self.colors["bg_alt"], border_width=1, border_color=self.colors["border"])
        txt_content.pack(fill="both", pady=(4, 12))

        btns = ctk.CTkFrame(frm, fg_color="transparent")
        btns.pack(anchor="e")

        def escolher_arquivo():
            path = filedialog.askopenfilename(title="Escolher anexo", filetypes=[("PDF", "*.pdf"), ("Todos", "*.*")])
            if path:
                # simple UI feedback
                btn_attach.configure(text="Anexo Selecionado")
                btn_attach.filepath = path

        btn_attach = ctk.CTkButton(btns, text="Escolher Arquivo", width=150, command=escolher_arquivo, fg_color=self.colors["bg_alt"], text_color=self.colors["text"])
        btn_attach.pack(side="left", padx=(0, 8))

        def salvar():
            title = entry_title.get().strip()
            content = txt_content.get("0.0", "end").strip()
            tag = entry_tag.get().strip() or "Geral"
            if not title:
                messagebox.showerror("Erro", "Informe o título do comunicado")
                return
            dados = {"title": title, "content": content, "tag": tag}
            # attach file path if selected (we just send path; service may be extended)
            if getattr(btn_attach, "filepath", None):
                dados["attachment_path"] = btn_attach.filepath
            self.criar_aviso(dados)
            modal.destroy()

        ctk.CTkButton(btns, text="Cancelar", width=120, command=modal.destroy, fg_color="transparent").pack(side="right", padx=8)
        ctk.CTkButton(btns, text="Salvar", width=120, command=salvar, fg_color=self.colors["primary"], text_color="white").pack(side="right")
