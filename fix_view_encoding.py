# -*- coding: utf-8 -*-
"""
fix_view_encoding.py
Corrige caracteres corrompidos de encoding UTF-8 em todos os arquivos de view.
Causa: bytes multi-byte de emojis foram re-interpretados isoladamente como Latin-1,
resultando em sequencias como Z, S, Z, », «, †, ‡, etc.
"""

import os

VIEWS_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\src\ser_pleno\presentation\views"

# Usamos unicode escapes para evitar qualquer problema de encoding no proprio script
# Mapeamento: (bytes corrompidos) -> ( caractere original correto )
REPLACEMENTS = {
    # ── comunicacao_interna.py ─────────────────────────────────────────────────
    "\U0001f600\u20134": "\U0001f4c1",   # 😀–¼ -> 📁  pasta
    "\U0001f600\u017d\u00a5": "\U0001f3a5",  # 😀Ž¥ -> 🎥  video
    "\U0001f600\u017d\u00b5": "\U0001f3b5",  # 😀Žµ -> 🎵  audio
    "\U0001f4ca\u0161": "\U0001f4ca",   # 📊Š  -> 📊  planilha
    "\U0001f4ca\u00bd": "\U0001f4ca",   # 📊½  -> 📊  apresentacao
    "\U0001f600\u2014\u0153": "\U0001f5dc",  # 😀—œ -> 🗜️ zip
    "\U0001f441\u00bb": "\U0001f4bb",   # 👁»  -> 💻  codigo
    "\U0001f600\u201d": "\U0001f50d",   # 😀”  -> 🔍  search
    "\U0001f4ca\u00b7": "\U0001f4ce",   # 📊·  -> 📎  paperclip
    "\U0001f4ca\u017e": "\U0001f4c4",   # 📊ž  -> 📄  doc
    "\u203a\u00ae": "\U0001f4e4",        # ‹®   -> 📤  send
    "\U0001f61f\u0160": "\U0001f600",   # 😟Š  -> 😀  emoji
    "\u00e2\u017e\u00a4": "\U0001f4eb", # âž¤ -> ⏫  upload
    "\U0001f4ca\u201e": "\U0001f4c4",   # 📊„  -> 📄  doc
    "\U0001f4ca\u00a5": "\U0001f4e5",   # 📊¥  -> 📥  download
    "\U0001f600\u2018": "\U0001f441",   # 😀‘  -> 👁  view

    # ── bem_estar.py ─────────────────────────────────────────────────────────
    "\U0001f61f\u00a2": "\U0001f61f",   # 😟¢ -> 😟  sad
    "\U0001f61f\u2022": "\U0001f61f",   # 😟• -> 😟  sad
    "\U0001f600\u203a\u00a1": "\U0001f600",  # 😀›¡ -> 😀 risk
    "\U0001f600\u0161\u00a8": "\U0001f600",  # 😀š¨ -> 😀 alert

    # ── estudantes.py ────────────────────────────────────────────────────────
    "\U0001f600\u017d\u201a": "\U0001f382",  # 😀Ž‚ -> 🎂 age
    "\U0001f600\u2018\u00a4": "\U0001f464",  # 😀‘¤ -> 👤 person

    # ── quadro_avisos.py ─────────────────────────────────────────────────────
    "\U0001f600\u00b7": "\U0001f4cc",   # 😀·  -> 📌  pin
    "\u00e2\u0161\u017e": "\U0001f5c2",  # âŠž  -> 🗂  layout
    "\u00e2\u2020\u2032": "\u2b06\ufe0f", # â†‘  -> ⬆️ up
    "\u00e2\u2020\u2033": "\u2b07\ufe0f", # â†"  -> ⬇️ down (aspas dupla no original)
    "\u00e2\u00b3": "\u23f3",           # â³   -> ⏳  loading
    "\U0001f4caLocal": "\U0001f4cd Local",  # 📊Local -> 📍 Local
    "\U0001f4ca  Hor\u00e1rio": "\U0001f570  Horário",  # 📊 Horário -> 🕐 Horário

    # ── orientacoes.py ───────────────────────────────────────────────────────
    "\u00e2\u00a7\u2030": "\U0001f5c2",  # â§‰ -> 🗂 duplicate
    "\U0001f600\u201d\u2014": "\U0001f5fa\ufe0f",  # 😀”— -> 🗺️ referral

    # ── relatorio.py ─────────────────────────────────────────────────────────
    "\U0001f4ca\u00a5": "\U0001f4e5",   # 📊¥  -> 📥  download

    # ── agenda.py ────────────────────────────────────────────────────────────
    "\u25cf\u20ac": "\u25c0",            # ●€  -> ◀  left arrow
    "\u2013\u00b6": "\u25b6",            # –¶  -> ▶  right arrow
    "\u26a1\u2122": "\u2699\ufe0f",      # ⚡™ -> ⚙️  gear

    # ── configuracoes.py ─────────────────────────────────────────────────────
    "\u2014\u00a2": "\u2014",           # —¢  -> —  em-dash
}

# Corrrecoes extras de texto (icon/aspas corrompidas em frases)
EXTRA_REPLACEMENTS = {
    "A  esquerda": "\u00e0 esquerda",   # -> à esquerda
    "A  direita": "\u00e0 direita",      # -> à direita
}

FILES_TO_PROCESS = [
    "comunicacao_interna.py",
    "bem_estar.py",
    "estudantes.py",
    "quadro_avisos.py",
    "orientacoes.py",
    "analise_triagem.py",
    "relatorio.py",
    "dashboard.py",
    "agenda.py",
    "configuracoes.py",
]

total_changes = 0
report = []

for fname in FILES_TO_PROCESS:
    fpath = os.path.join(VIEWS_DIR, fname)
    if not os.path.exists(fpath):
        report.append("[SKIP] {}: arquivo não encontrado".format(fname))
        continue

    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    original = content
    changes = 0

    for old, new in REPLACEMENTS.items():
        count = content.count(old)
        if count:
            content = content.replace(old, new)
            changes += count

    for old, new in EXTRA_REPLACEMENTS.items():
        count = content.count(old)
        if count:
            content = content.replace(old, new)
            changes += count

    if content != original:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        report.append("[FIXED] {}: {} correc\u00e7\u00e3o(\u00f5es) aplicada(s)".format(fname, changes))
    else:
        report.append("[OK]    {}: sem altera\u00e7\u00f5es necess\u00e1rias".format(fname))

    total_changes += changes

print("\n".join(report))
print("\nTotal de corre\u00e7\u00f5es em todos os arquivos: {}".format(total_changes))
