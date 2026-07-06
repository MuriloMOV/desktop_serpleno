# -*- coding: utf-8 -*-
"""
Diagnostica e corrige bytes inválidos (U+FFFD) em src/ser_pleno/**/*.py
"""
from pathlib import Path

ROOT = Path(r"C:\Users\58023826\Desktop\react\tkinter\desktop_serpleno\src\ser_pleno")

suspects = [
    "presentation/components/ui_components.py",
    "presentation/views/agenda.py",
    "presentation/views/analise_triagem.py",
    "presentation/views/comunicacao_interna.py",
    "presentation/views/dashboard.py",
    "presentation/views/estudantes.py",
    "presentation/views/login.py",
    "presentation/views/orientacoes.py",
    "presentation/views/quadro_avisos.py",
]

for rel in suspects:
    path = ROOT / rel
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
        if "\ufffd" not in text:
            print(f"{rel}: OK, sem U+FFFD")
            continue
        print(f"\n== {rel}: TEM U+FFFD ==")
        for i, ch in enumerate(text):
            if ch == "\ufffd":
                # Mostra contexto ao redor
                start = max(0, i - 30)
                end = min(len(text), i + 30)
                ctx = text[start:end]
                print(f"  pos {i}: ...{repr(ctx)}...")
                # Mostra bytes ao redor
                byte_pos = len(text[:i].encode("utf-8"))
                byte_start = max(0, byte_pos - 10)
                byte_end = min(len(raw), byte_pos + 10)
                print(f"  bytes[{byte_start}:{byte_end}]: {raw[byte_start:byte_end].hex()}")
    except UnicodeDecodeError as e:
        print(f"\n== {rel}: ERRO DECODE == {e}")
        # Mostra bytes ao redor do erro
        start = max(0, e.start - 16)
        end = min(len(raw), e.end + 16)
        print(f"  bytes[{start}:{end}]: {raw[start:end].hex()}")
