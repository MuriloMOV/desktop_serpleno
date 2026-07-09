# -*- coding: utf-8 -*-
"""
fix_view_encoding_v2.py — Corrige caracteres corrompidos de encoding nos arquivos de view.
Estratégia: verifica sintaxe Python + detecta substituições especificas.
"""

import os
import re
import ast
import shutil
from datetime import datetime

VIEWS_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\src\ser_pleno\presentation\views"
BACKUP_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\.backup_views_encoding_fix"

FILES = [
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

# ─── Mapeamento específico (string corrompida -> correta) ─────────────────────
# Chave = sequencia EXATA de caracteres corrompidos encontrada no arquivo
REPLACEMENTS = {
    # comunicacao_interna.py
    "\U0001f600\u20134": "\U0001f4c1",   # 😀–¼ -> 📁
    "\U0001f600\u017d\u00a5": "\U0001f3a5",  # 😀Ž¥ -> 🎥
    "\U0001f600\u017d\u00b5": "\U0001f3b5",  # 😀Žµ -> 🎵
    "\U0001f4ca\u0161": "\U0001f4ca",    # 📊Š -> 📊
    "\U0001f4ca\u00bd": "\U0001f4ca",    # 📊½ -> 📊
    "\U0001f600\u2014\u0153": "\U0001f5dc",  # 😀—œ -> 🗜
    "\U0001f441\u00bb": "\U0001f4bb",    # 👁» -> 💻
    "\U0001f600\u201d": "\U0001f50d",    # 😀” -> 🔍
    "\U0001f4ca\u00b7": "\U0001f4ce",    # 📊· -> 📎
    "\U0001f4ca\u017e": "\U0001f4c4",    # 📊ž -> 📄
    "\u203a\u00ae": "\U0001f4e4",         # ‹® -> 📤
    "\U0001f61f\u0160": "\U0001f600",    # 😟Š -> 😀
    "\u00e2\u017e\u00a4": "\U0001f4eb",  # âž¤ -> ⏫
    "\U0001f4ca\u201e": "\U0001f4c4",    # 📊„ -> 📄
    "\U0001f4ca\u00a5": "\U0001f4e5",    # 📊¥ -> 📥
    "\U0001f600\u2018": "\U0001f441",    # 😀‘ -> 👁
    "\U0001f4ca\u201c": "\U0001f4ca",    # 📊“ -> 📊

    # bem_estar.py
    "\U0001f61f\u00a2": "\U0001f61f",   # 😟¢ -> 😟
    "\U0001f61f\u2022": "\U0001f61f",   # 😟• -> 😟
    "\U0001f600\u203a\u00a1": "\U0001f600",  # 😀›¡ -> 😀
    "\U0001f600\u0161\u00a8": "\U0001f600",  # 😀š¨ -> 😀

    # estudantes.py
    "\U0001f600\u017d\u201a": "\U0001f382",  # 😀Ž‚ -> 🎂
    "\U0001f600\u2018\u00a4": "\U0001f464",  # 😀‘¤ -> 👤

    # quadro_avisos.py
    "\U0001f600\u00b7": "\U0001f4cc",   # 😀· -> 📌
    "\u00e2\u0161\u017e": "\U0001f5c2",  # âŠž -> 🗂
    "\u00e2\u2020\u2032": "\u2b06\ufe0f", # â†‘ -> ⬆️
    "\u00e2\u2020\u2033": "\u2b07\ufe0f", # â†" -> ⬇️
    "\u00e2\u00b3": "\u23f3",            # â³ -> ⏳
    "\U0001f4caLocal": "\U0001f4cd Local",  # 📊Local -> 📍 Local
    "\u00e2\u00a7\u2030": "\U0001f5c2",  # â§‰ -> 🗂

    # orientacoes.py
    "\U0001f600\u201d\u2014": "\U0001f5fa\ufe0f",  # 😀"— -> 🗺

    # analise_triagem.py
    "\u00e2\u00b3": "\u23f3",            # â³ -> ⏳

    # relatorio.py

    # agenda.py
    "\u25cf\u20ac": "\u25c0",            # ●€ -> ◀
    "\u2013\u00b6": "\u25b6",            # –¶ -> ▶
    "\u26a1\u2122": "\u2699\ufe0f",      # ⚡™ -> ⚙️

    # configuracoes.py
    "\u2014\u00a2": "\u2014",            # —¢ -> —
}

# ─── Fixes de texto (não ícone, mas palavra/typo corrompida) ─────────────────
EXTRA_REPLACEMENTS = {
    # quadro_avisos.py — "A esquerda" -> "à esquerda" (çao → espaco + acento)
    "A  esquerda": "\u00e0 esquerda",
    "A  direita": "\u00e0 direita",
    # Comentários com  em-dash corrompido (aspas curvas no lugar)
    # Estes sao SOBRESCRITOS pelos REPLACEMENTS acima para nao duplicar
}


def detect_broken_chars(content):
    """Retorna True se ha caracteres corrompidos (fora do range ASCII + latin-1 + emojis comuns)."""
    # Caracteres que indicam corrupcao LATIN-1 de bytes UTF-8:
    broken_chars = set("\u017d\u017e\u0161\u0153\u201e\u201c\u2018\u2019"
                       "\u00a2\u00b6\u00a4\u00a5\u00bd\u00b7\u2022"
                       "\u203a\u00ae\u2030\u20ac\u25cf\u2122"
                       "\u2014\u201d\u00ab\u00bb\u2033\u2032")
    for ch in content:
        if ch in broken_chars:
            return True
    return False


def check_syntax(fpath):
    """Verifica se o arquivo Python e sintaticamente valido."""
    try:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


os.makedirs(BACKUP_DIR, exist_ok=True)

results = []
total_replacements = 0

for fname in FILES:
    fpath = os.path.join(VIEWS_DIR, fname)
    if not os.path.exists(fpath):
        results.append("[SKIP] {} — arquivo nao encontrado".format(fname))
        continue

    # 1) Verificar sintaxe antes
    ok_before, err_before = check_syntax(fpath)

    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    original = content
    changes = 0
    detail = []

    # 2) Aplicar REPLACEMENTS
    for old, new in REPLACEMENTS.items():
        count = content.count(old)
        if count:
            content = content.replace(old, new)
            changes += count
            detail.append("{}x {} -> {}".format(count, repr(old[:8]), repr(new[:8])))

    # 3) Aplicar EXTRA_REPLACEMENTS
    for old, new in EXTRA_REPLACEMENTS.items():
        count = content.count(old)
        if count:
            content = content.replace(old, new)
            changes += count
            detail.append("{}x {} -> {}".format(count, repr(old), repr(new)))

    if content != original:
        # Backup
        backup_path = os.path.join(BACKUP_DIR, fname)
        shutil.copy2(fpath, backup_path)

        # Escrever arquivo corrigido
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)

        # Verificar sintaxe depois
        ok_after, err_after = check_syntax(fpath)

        status = "OK" if ok_after else "SYNTAX ERROR: {}".format(err_after)
        results.append("[FIXED] {} — {} correcões | sintaxe: {}".format(
            fname, changes, status))
        for d in detail:
            results.append("       " + d)
    else:
        results.append("[OK]    {} — sem alteracoes (sintaxe antiga: {})".format(
            fname, "valida" if ok_before else "INVALIDA(!)"))

    total_replacements += changes

print("\n".join(results))
print("\n{} Total de substituicoes em todos os arquivos.".format(total_replacements))
print("\nBackups salvos em: {}".format(BACKUP_DIR))
