# -*- coding: utf-8 -*-
import os, ast, shutil
from datetime import datetime

VIEWS_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\src\ser_pleno\presentation\views"
BACKUP_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\.backup_views_encoding_fix"
LOG = r"F:\Projetos\mobile-web-desk\desktop_serpleno\fix_log.txt"

FILES = [
    "comunicacao_interna.py","bem_estar.py","estudantes.py","quadro_avisos.py",
    "orientacoes.py","analise_triagem.py","relatorio.py","dashboard.py",
    "agenda.py","configuracoes.py",
]

REPLACEMENTS = {
    # comunicacao_interna.py
    "\U0001f600\u20134": "\U0001f4c1",
    "\U0001f600\u017d\u00a5": "\U0001f3a5",
    "\U0001f600\u017d\u00b5": "\U0001f3b5",
    "\U0001f4ca\u0161": "\U0001f4ca",
    "\U0001f4ca\u00bd": "\U0001f4ca",
    "\U0001f600\u2014\u0153": "\U0001f5dc",
    "\U0001f441\u00bb": "\U0001f4bb",
    "\U0001f600\u201d": "\U0001f50d",
    "\U0001f4ca\u00b7": "\U0001f4ce",
    "\U0001f4ca\u017e": "\U0001f4c4",
    "\u203a\u00ae": "\U0001f4e4",
    "\U0001f61f\u0160": "\U0001f600",
    "\u00e2\u017e\u00a4": "\U0001f4eb",
    "\U0001f4ca\u201e": "\U0001f4c4",
    "\U0001f4ca\u00a5": "\U0001f4e5",
    "\U0001f600\u2018": "\U0001f441",
    # bem_estar.py
    "\U0001f61f\u00a2": "\U0001f61f",
    "\U0001f61f\u2022": "\U0001f61f",
    "\U0001f600\u203a\u00a1": "\U0001f600",
    "\U0001f600\u0161\u00a8": "\U0001f600",
    # estudantes.py
    "\U0001f600\u017d\u201a": "\U0001f382",
    "\U0001f600\u2018\u00a4": "\U0001f464",
    # quadro_avisos.py
    "\U0001f600\u00b7": "\U0001f4cc",
    "\u00e2\u0161\u017e": "\U0001f5c2",
    "\u00e2\u2020\u2032": "\u2b06\ufe0f",
    "\u00e2\u2020\u2033": "\u2b07\ufe0f",
    "\u00e2\u00b3": "\u23f3",
    "\U0001f4caLocal": "\U0001f4cd Local",
    "\u00e2\u00a7\u2030": "\U0001f5c2",
    # orientacoes.py
    "\U0001f600\u201d\u2014": "\U0001f5fa\ufe0f",
    # agenda.py
    "\u25cf\u20ac": "\u25c0",
    "\u2013\u00b6": "\u25b6",
    "\u26a1\u2122": "\u2699\ufe0f",
    # configuracoes.py
    "\u2014\u00a2": "\u2014",
}

EXTRA_REPLACEMENTS = {
    "A  esquerda": "\u00e0 esquerda",
    "A  direita": "\u00e0 direita",
}

def check_syntax(fpath):
    try:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
        ast.parse(source)
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

        for old, new in REPLACEMENTS.items():
            count = content.count(old)
            if count:
                content = content.replace(old, new)
                changes += count
                detail.append("  {:3d}x  [{}] -> [{}]".format(
                    count,
                    ":".join("{:02x}".format(ord(c)) for c in old[:6]),
                    ":".join("{:02x}".format(ord(c)) for c in new[:6]),
                ))

        for old, new in EXTRA_REPLACEMENTS.items():
            count = content.count(old)
            if count:
                content = content.replace(old, new)
                changes += count
                detail.append("  {:3d}x  '{}' -> '{}'".format(count, old, new))

        if content != original:
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
        f.write("FIX LOG - {}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write("=" * 60 + "\n\n")
        f.writelines(lines)
        f.write("\nTotal substituicoes: {}\n".format(total))
        f.write("Backups em: {}\n".format(BACKUP_DIR))

main()
