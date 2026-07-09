# -*- coding: latin-1 -*-
"""
fix_encoding_final.py — Corrige caracteres corrompidos de encoding nos views.
Estratégia: regex para padroes corrompidos + substituicao literal.
Todos os padroes sao extraidos dos hex bytes reais dos arquivos.
"""

import os, re, ast, shutil

VIEWS_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\src\ser_pleno\presentation\views"
BACKUP_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\.backup_views_encoding_fix"
LOG = r"F:\Projetos\mobile-web-desk\desktop_serpleno\fix_log_final.txt"

FILES = [
    "comunicacao_interna.py","bem_estar.py","estudantes.py","quadro_avisos.py",
    "orientacoes.py","analise_triagem.py","relatorio.py","dashboard.py",
    "agenda.py","configuracoes.py",
]

# ── Mapeamento: sequencia corrompida -> correta ──────────────────────────────
# Prefixo emoji: 0xf0 0x9f 0x98 0x80 = U+1F600 grinning face
REPLACEMENTS = {
    # comunicacao_interna.py
    "\U0001f600\u2013\u00bc": "\U0001f4c1",   # 😀–¼ -> 📁 file-folder
    "\U0001f600\u017d\u00a5": "\U0001f3a5",   # 😀Ž¥ -> 🎥 movie-camera
    "\U0001f600\u017d\u00b5": "\U0001f3b5",   # 😀Žµ -> 🎵 music note
    "\U0001f600\u2014\u0153": "\U0001f5dc",   # 😀—œ -> 🗜 compress
    "\U0001f600\u2013\u201c": "\U0001f4cc",   # 😀–" -> 📎 paperclip (no comment, icon)
    "\U0001f600\u2018":       "\U0001f441",   # 😀'  -> 👁 eye
    "\U0001f600\u201d":       "\U0001f50d",   # 😀"  -> 🔍 search
    "\U0001f600\u201d\u2014": "\U0001f5fa\ufe0f",  # 😀"— -> 🗺 map
    "\U0001f600\u201c":       "\U0001f4ca",   # 😀"  -> 📊 chart (used as local/clock fallback)
    "\U0001f600\u203a\u00a1": "\U0001f600",   # 😀›¡ -> 😀 generic
    "\U0001f600\u0161\u00a8": "\U0001f600",   # 😀š¨ -> 😀 generic
    # repeated variants
    "\U0001f600\u203a": "\U0001f600",          # 😀›  -> 😀

    # bem_estar.py
    "\U0001f61f\u00a2": "\U0001f61f",          # 😟¢ -> 😟
    "\U0001f61f\u2022": "\U0001f61f",          # 😟• -> 😟
    "\U0001f61f\u0160": "\U0001f600",          # 😟Š -> 😀

    # estudantes.py
    "\U0001f600\u017d\u201a": "\U0001f382",    # 😀Ž‚ -> 🎂
    "\U0001f600\u2018\u00a4": "\U0001f464",    # 😀‘¤ -> 👤

    # quadro_avisos.py
    "\U0001f600\u00b7":  "\U0001f4cc",         # 😀· -> 📌
    "\U0001f4caLocal":    "\U0001f4cd Local",   # 📊Local -> 📍 Local
    "\U0001f4ca\u00a5":  "\U0001f4e5",         # 📊¥ -> 📥 download

    # orientacoes.py
    "\u00e2\u00a7\u2030": "\U0001f5c2",        # â§‰ -> 🗂
    "\U0001f600\u00b7":  "\U0001f4cc",         # 😀· -> 📌

    # analise_triagem.py
    "\u00e2\u00b3": "\u23f3",                   # â³ -> ⏳
    "\U0001f600\u017d\u201a": "\U0001f382",    # 😀Ž‚ -> 🎂
    "\U0001f600\u2018\u00a4": "\U0001f464",    # 😀‘¤ -> 👤

    # relatorio.py
    "\U0001f4ca\u00a5": "\U0001f4e5",          # 📊¥ -> 📥

    # agenda.py
    "\u25cf\u20ac": "\u25c0",                   # ●€ -> ◀
    "\u2013\u00b6": "\u25b6",                   # –¶ -> ▶
    "\u26a1\u2122": "\u2699\ufe0f",             # ⚡™ -> ⚙️

    # configuracoes.py
    "\u2014\u00a2": "\u2014",                   # —¢ -> —

    # bem_estar.py set_value placeholders (em-dash próprio válido, keep —)
    # bem_estar.py:  confirmar que “—” nos set_value sao em-dash legitimos
}

# Fixes extras de texto
EXTRA_REPLACEMENTS = {
    "A  esquerda": "\u00e0 esquerda",
    "A  direita": "\u00e0 direita",
}

# ── Padrões regex: casos onde o prefixo emoji varia ─────────────────────────
# (\U0001f4ca = 📊) em bugs que aparecem como prefixo errado
ICON_PREFIX_REPLACEMENTS = {
    # 📊 + caractere corrompido (Latin-1 byte decorruptivado)
    "\U0001f4ca\u0161": "\U0001f4ca",     # 📊Š -> 📊
    "\U0001f4ca\u00bd": "\U0001f4ca",     # 📊½ -> 📊
    "\U0001f4ca\u00b7": "\U0001f4ce",     # 📊· -> 📎
    "\U0001f4ca\u017e": "\U0001f4c4",     # 📊ž -> 📄
    "\U0001f4ca\u201c": "\U0001f4ca",     # 📊“ -> 📊 (emitida como bar chart)
    "\U0001f4ca\u201e": "\U0001f4c4",     # 📊„ -> 📄 doc
    # 👁 + caractere corrompido
    "\U0001f441\u00bb": "\U0001f4bb",     # 👁» -> 💻
    # symbols with corrupted suffix
    "\u25cf\u20ac": "\u25c0",             # ●€ -> ◀
    "\u2013\u00b6": "\u25b6",             # –¶ -> ▶
    "\u26a1\u2122": "\u2699\ufe0f",       # ⚡™ -> ⚙️
}

def check_syntax(fpath):
    try:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            ast.parse(f.read())
        return True, "OK"
    except SyntaxError as e:
        return False, "linha {}: {}".format(e.lineno, e.msg)
    except Exception as e:
        return False, str(e)

def main():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    lines = []
    total = 0

    for fname in FILES:
        fpath = os.path.join(VIEWS_DIR, fname)
        if not os.path.exists(fpath):
            lines.append("[SKIP] {} -- not found\n".format(fname))
            continue

        ok_before, err_before = check_syntax(fpath)

        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        original = content
        changes = 0
        detail = []

        # Apply all replacement dicts
        for d in [REPLACEMENTS, ICON_PREFIX_REPLACEMENTS, EXTRA_REPLACEMENTS]:
            for old, new in d.items():
                count = content.count(old)
                if count:
                    content = content.replace(old, new)
                    changes += count
                    hex_o = ":".join("{:04x}".format(ord(c)) for c in old[:8])
                    hex_n = ":".join("{:04x}".format(ord(c)) for c in new[:4])
                    detail.append("  {:3d}x  hex[{}] -> [{}]".format(count, hex_o, hex_n))

        if content != original:
            # backup original
            shutil.copy2(fpath, os.path.join(BACKUP_DIR, fname))
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            ok_after, err_after = check_syntax(fpath)
            status = "syntax OK" if ok_after else "SYNTAX ERROR " + err_after
            lines.append("[FIXED] {} -- {:3d} changes | {}\n".format(fname, changes, status))
            lines.extend(["       " + d + "\n" for d in detail])
        else:
            syn = "syntax OK" if ok_before else "syntax BROKEN(!)"
            lines.append("[OK]    {} -- 0 changes | {}\n".format(fname, syn))

        total += changes

    with open(LOG, "w", encoding="utf-8") as f:
        f.write("FIX LOG - {}\n".format(
            __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write("=" * 60 + "\n\n")
        f.writelines(lines)
        f.write("\nTotal subst: {}\n".format(total))

main()
