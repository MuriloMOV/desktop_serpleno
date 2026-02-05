# agenda_desktop.py
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import requests
from datetime import datetime, timedelta
import locale


# --- CONFIGURAÇÕES ---
API_BASE = "http://127.0.0.1:8000"  # ajuste para seu backend Django
LOCALE = "pt_BR.UTF-8"  # para formatação de datas (ajuste conforme sistema)
try:
    locale.setlocale(locale.LC_TIME, LOCALE)
except Exception:
    pass

# Design tokens
TOKENS = {
    "color_primary": "#0B5FFF",
    "accent": "#00B37E",
    "bg": "#F6F7FB",
    "text": "#0F1724",
    "muted": "#6B7280",
    "border": "#E6E9F2",
    "error": "#E02424",
    "radius": 8,
    "padding": 16
}

# --- API CLIENT (simples) ---
class ApiClient:
    def __init__(self, base_url):
        self.base = base_url.rstrip("/")

    def _get(self, path, params=None):
        url = f"{self.base}{path}"
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        return r.json()

    def _post(self, path, json):
        url = f"{self.base}{path}"
        r = requests.post(url, json=json, timeout=8)
        r.raise_for_status()
        return r.json()

    def _delete(self, path, params=None):
        url = f"{self.base}{path}"
        r = requests.delete(url, params=params, timeout=8)
        r.raise_for_status()
        return r

    # endpoints esperados
    def get_timeslots(self, weekday):
        return self._get(f"/api/timeslots/{weekday}")

    def get_bookings(self, date_str):
        return self._get(f"/api/bookings/{date_str}")

    def get_students(self):
        return self._get("/api/students")

    def create_timeslot(self, start, end, weekday):
        return self._post("/api/timeslot", {"start": start, "end": end, "weekday": weekday})

    def delete_timeslot(self, id_):
        return self._delete("/api/timeslot", params={"id": id_})

    def create_booking(self, date, timeslot_id, student_id, notes):
        return self._post("/api/booking", {"date": date, "timeslot_id": timeslot_id, "student_id": student_id, "notes": notes})

    def delete_booking(self, id_):
        return self._delete("/api/booking", params={"id": id_})

# --- UTILITÁRIOS ---
def run_in_thread(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=lambda: fn(*args, **kwargs), daemon=True).start()
    return wrapper

def format_date_label(d: datetime):
    # ex: quinta-feira, 05 de fevereiro
    try:
        return d.strftime("%A, %d de %B").capitalize()
    except Exception:
        return d.strftime("%d/%m/%Y")

# --- MODAIS ---
class ManageTimesModal(ctk.CTkToplevel):
    def __init__(self, parent, api: ApiClient, on_change=None):
        super().__init__(parent)
        self.title("Gerir horários")
        self.geometry("520x420")
        self.api = api
        self.on_change = on_change
        self.configure(padx=16, pady=16)
        self.build_ui()
        self.load_weekday( (datetime.now().weekday()) )

    def build_ui(self):
        header = ctk.CTkLabel(self, text="Gerir horários", font=ctk.CTkFont(size=16, weight="bold"))
        header.pack(anchor="w", pady=(0,12))

        row = ctk.CTkFrame(self)
        row.pack(fill="x", pady=(0,12))
        self.weekday_var = ctk.StringVar(value=str(datetime.now().weekday()))
        weekdays = [("Seg",0),("Ter",1),("Qua",2),("Qui",3),("Sex",4),("Sáb",5),("Dom",6)]
        for name, val in weekdays:
            rb = ctk.CTkRadioButton(row, text=name, variable=self.weekday_var, value=str(val), command=self._on_weekday_change)
            rb.pack(side="left", padx=6)

        # list of timeslots
        self.list_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        self.list_frame.pack(fill="both", expand=True, pady=(0,12))
        self.timeslot_listbox = tk.Listbox(self.list_frame, bd=0, highlightthickness=0)
        self.timeslot_listbox.pack(fill="both", expand=True, padx=8, pady=8)

        # add form
        form = ctk.CTkFrame(self)
        form.pack(fill="x", pady=(0,8))
        self.start_entry = ctk.CTkEntry(form, placeholder_text="Início (HH:MM)")
        self.start_entry.pack(side="left", padx=(0,8), expand=True, fill="x")
        self.end_entry = ctk.CTkEntry(form, placeholder_text="Fim (HH:MM)")
        self.end_entry.pack(side="left", padx=(0,8), expand=True, fill="x")
        add_btn = ctk.CTkButton(form, text="Adicionar", command=self._add_timeslot, fg_color=TOKENS["accent"])
        add_btn.pack(side="left")

        del_btn = ctk.CTkButton(self, text="Remover selecionado", command=self._remove_selected, fg_color="#E02424")
        del_btn.pack(fill="x")

    def _on_weekday_change(self):
        self.load_weekday(int(self.weekday_var.get()))

    @run_in_thread
    def load_weekday(self, weekday):
        try:
            slots = self.api.get_timeslots(weekday)
            def ui_update():
                self.timeslot_listbox.delete(0, tk.END)
                for s in slots:
                    label = f"{s['id']} — {s['start']} → {s['end']}"
                    self.timeslot_listbox.insert(tk.END, label)
            self.after(0, ui_update)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", f"Falha ao carregar horários:\n{e}"))

    @run_in_thread
    def _add_timeslot(self):
        start = self.start_entry.get().strip()
        end = self.end_entry.get().strip()
        weekday = int(self.weekday_var.get())
        if not start or not end:
            messagebox.showwarning("Atenção", "Preencha início e fim.")
            return
        try:
            self.api.create_timeslot(start, end, weekday)
            self.load_weekday(weekday)
            if self.on_change:
                self.on_change()
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", f"Não foi possível adicionar:\n{e}"))

    @run_in_thread
    def _remove_selected(self):
        sel = self.timeslot_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Selecione um horário para remover.")
            return
        item = self.timeslot_listbox.get(sel[0])
        id_ = item.split("—")[0].strip()
        try:
            self.api.delete_timeslot(id_)
            self.load_weekday(int(self.weekday_var.get()))
            if self.on_change:
                self.on_change()
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", f"Não foi possível remover:\n{e}"))

class BookingModal(ctk.CTkToplevel):
    def __init__(self, parent, api: ApiClient, date_str, timeslot, on_saved=None):
        super().__init__(parent)
        self.title("Agendar estudante")
        self.geometry("420x300")
        self.api = api
        self.date_str = date_str
        self.timeslot = timeslot
        self.on_saved = on_saved
        self.configure(padx=16, pady=16)
        self.build_ui()
        self.load_students()

    def build_ui(self):
        lbl = ctk.CTkLabel(self, text=f"Horário: {self.timeslot['start']} → {self.timeslot['end']}", font=ctk.CTkFont(size=14, weight="bold"))
        lbl.pack(anchor="w", pady=(0,12))
        self.student_cb = ctk.CTkComboBox(self, values=[], width=360)
        self.student_cb.pack(fill="x", pady=(0,8))
        self.notes = ctk.CTkTextbox(self, height=100)
        self.notes.pack(fill="both", pady=(0,8))
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x")
        save_btn = ctk.CTkButton(btn_frame, text="Salvar", fg_color=TOKENS["color_primary"], command=self._save)
        save_btn.pack(side="right", padx=(8,0))
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancelar", command=self.destroy, fg_color="gray20")
        cancel_btn.pack(side="right")

    @run_in_thread
    def load_students(self):
        try:
            students = self.api.get_students()
            names = [f"{s['id']} - {s['name']}" for s in students]
            self.after(0, lambda: self.student_cb.configure(values=names))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", f"Falha ao carregar estudantes:\n{e}"))

    @run_in_thread
    def _save(self):
        sel = self.student_cb.get()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um estudante.")
            return
        student_id = int(sel.split("-")[0].strip())
        notes = self.notes.get("1.0", "end").strip()
        try:
            self.api.create_booking(self.date_str, self.timeslot['id'], student_id, notes)
            if self.on_saved:
                self.on_saved()
            self.after(0, lambda: self.destroy())
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", f"Não foi possível salvar:\n{e}"))

# --- APLICAÇÃO PRINCIPAL ---
class AgendaApp(ctk.CTk):
    def __init__(self, api: ApiClient):
        super().__init__()
        self.api = api
        self.title("Agenda")
        self.geometry("1100x760")
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")
        self.configure(padx=24, pady=24, fg_color=TOKENS["bg"])
        self.selected_date = datetime.now().date()
        self.build_ui()
        self.refresh_all()

    def build_ui(self):
        # Header
        header = ctk.CTkFrame(self, height=72, fg_color="white", corner_radius=TOKENS["radius"])
        header.pack(fill="x", pady=(0,16))
        header.grid_columnconfigure(0, weight=1)
        title = ctk.CTkLabel(header, text="Agenda", font=ctk.CTkFont(size=20, weight="bold"))
        title.place(relx=0.5, rely=0.5, anchor="center")
        # icons right
        icons_frame = ctk.CTkFrame(header, fg_color="transparent")
        icons_frame.place(relx=0.98, rely=0.5, anchor="e")
        for txt in ["🤝","🔔","👤","⏻"]:
            b = ctk.CTkButton(icons_frame, text=txt, width=36, height=36, corner_radius=6, fg_color="transparent", hover_color=TOKENS["border"])
            b.pack(side="left", padx=6)

        # Top container with calendar icon, title/subtitle and day selector + manage button
        top = ctk.CTkFrame(self, fg_color="white", corner_radius=TOKENS["radius"])
        top.pack(fill="x", pady=(0,16))
        top.grid_columnconfigure(1, weight=1)
        # left: icon + texts
        left = ctk.CTkFrame(top, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=16, pady=16)
        icon_lbl = ctk.CTkLabel(left, text="📅", font=ctk.CTkFont(size=28))
        icon_lbl.pack(side="left", padx=(0,12))
        texts = ctk.CTkFrame(left, fg_color="transparent")
        texts.pack(side="left")
        t1 = ctk.CTkLabel(texts, text="Agenda de horários", font=ctk.CTkFont(size=14, weight="bold"))
        t1.pack(anchor="w")
        self.subtitle_lbl = ctk.CTkLabel(texts, text=format_date_label(datetime.now()), font=ctk.CTkFont(size=12), text_color=TOKENS["muted"])
        self.subtitle_lbl.pack(anchor="w")

        # center: day selector
        center = ctk.CTkFrame(top, fg_color="transparent")
        center.grid(row=0, column=1, sticky="ew")
        self.date_entry = ctk.CTkEntry(center, width=260)
        self.date_entry.pack(pady=18)
        self.date_entry.insert(0, self.selected_date.isoformat())
        go_btn = ctk.CTkButton(center, text="Ir", command=self._on_date_change)
        go_btn.pack(pady=6)

        # right: manage button
        right = ctk.CTkFrame(top, fg_color="transparent")
        right.grid(row=0, column=2, sticky="e", padx=16)
        manage_btn = ctk.CTkButton(right, text="Gerir horários", fg_color=TOKENS["color_primary"], command=self._open_manage_modal)
        manage_btn.pack(pady=18)

        # Main panels: left details (not used heavily) and right lists
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)

        # Agenda do dia
        day_card = ctk.CTkFrame(main, fg_color="white", corner_radius=TOKENS["radius"])
        day_card.grid(row=0, column=0, sticky="nsew", padx=(0,12), pady=8)
        day_card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(day_card, text="Agenda do dia", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w", padx=16, pady=(12,0))
        self.grid_day_frame = ctk.CTkFrame(day_card, fg_color="transparent")
        self.grid_day_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)

        # Próxima semana
        week_card = ctk.CTkFrame(main, fg_color="white", corner_radius=TOKENS["radius"])
        week_card.grid(row=0, column=1, sticky="nsew", padx=(12,0), pady=8)
        week_card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(week_card, text="Próxima semana", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w", padx=16, pady=(12,0))
        self.grid_week_frame = ctk.CTkFrame(week_card, fg_color="transparent")
        self.grid_week_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)

        # floating new button
        new_btn = ctk.CTkButton(self, text="+", width=56, height=56, corner_radius=28, fg_color=TOKENS["accent"], command=self._open_manage_modal)
        new_btn.place(relx=0.95, rely=0.92, anchor="center")

    def _on_date_change(self):
        try:
            d = datetime.fromisoformat(self.date_entry.get()).date()
            self.selected_date = d
            self.subtitle_lbl.configure(text=format_date_label(datetime.combine(d, datetime.min.time())))
            self.refresh_all()
        except Exception:
            messagebox.showerror("Erro", "Formato de data inválido. Use YYYY-MM-DD.")

    def _open_manage_modal(self):
        ManageTimesModal(self, self.api, on_change=self.refresh_all)

    def _open_booking_modal(self, date_str, timeslot):
        BookingModal(self, self.api, date_str, timeslot, on_saved=self.refresh_all)

    @run_in_thread
    def refresh_all(self):
        # carrega timeslots do dia (weekday) e bookings do dia e da próxima semana
        try:
            weekday = self.selected_date.weekday()
            timeslots = self.api.get_timeslots(weekday)
            bookings = self.api.get_bookings(self.selected_date.isoformat())
            # próxima semana: same weekday +7
            next_date = self.selected_date + timedelta(days=7)
            next_weekday = next_date.weekday()
            timeslots_next = self.api.get_timeslots(next_weekday)
            bookings_next = self.api.get_bookings(next_date.isoformat())

            def ui_update():
                self._render_grid(self.grid_day_frame, timeslots, bookings, self.selected_date)
                self._render_grid(self.grid_week_frame, timeslots_next, bookings_next, next_date)
            self.after(0, ui_update)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", f"Falha ao atualizar:\n{e}"))

    def _render_grid(self, container, timeslots, bookings, date_obj):
        # limpa
        for w in container.winfo_children():
            w.destroy()
        # map bookings por timeslot
        booking_map = {b['timeslot_id']: b for b in bookings}
        # grid: vertical list de timeslots (pode ser adaptado para grid visual)
        for idx, ts in enumerate(timeslots):
            frame = ctk.CTkFrame(container, fg_color="white", corner_radius=6, height=72)
            frame.pack(fill="x", pady=6)
            frame.grid_propagate(False)
            left = ctk.CTkFrame(frame, width=8, fg_color=TOKENS["accent"])
            left.pack(side="left", fill="y")
            info = ctk.CTkLabel(frame, text=f"{ts['start']} → {ts['end']}", font=ctk.CTkFont(size=14, weight="bold"))
            info.pack(anchor="w", padx=12, pady=8)
            # booking info
            b = booking_map.get(ts['id'])
            if b:
                student_name = b.get('student_name') or str(b.get('student_id'))
                lbl = ctk.CTkLabel(frame, text=f"{student_name}", text_color=TOKENS["muted"])
                lbl.pack(anchor="w", padx=12)
                action = ctk.CTkButton(frame, text="Ver / Cancelar", width=120, command=lambda bid=b['id']: self._cancel_booking_confirm(bid))
                action.pack(side="right", padx=12)
            else:
                book_btn = ctk.CTkButton(frame, text="Agendar", fg_color=TOKENS["color_primary"],
                                         command=lambda ts=ts, d=date_obj: self._open_booking_modal(d.isoformat(), ts))
                book_btn.pack(side="right", padx=12)

    @run_in_thread
    def _cancel_booking_confirm(self, booking_id):
        # confirmação em thread -> UI via after
        def ask():
            if messagebox.askyesno("Confirmar", "Deseja cancelar este agendamento?"):
                try:
                    self.api.delete_booking(booking_id)
                    self.refresh_all()
                except Exception as e:
                    messagebox.showerror("Erro", f"Não foi possível cancelar:\n{e}")
        self.after(0, ask)

# --- EXECUÇÃO ---
def main():
    api = ApiClient(API_BASE)
    app = AgendaApp(api)
    app.mainloop()

if __name__ == "__main__":
    main()
