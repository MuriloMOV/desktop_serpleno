# -*- coding: utf-8 -*-
"""
profiler.py — mostra os codepoints exatos de cada caractere
em cada linha dos arquivos de view que contem caracteres suspeitos.
"""
import os

VIEWS_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\src\ser_pleno\presentation\views"
OUT = r"F:\Projetos\mobile-web-desk\desktop_serpleno\char_profile.txt"

FILES = [
    "comunicacao_interna.py","bem_estar.py","estudantes.py","quadro_avisos.py",
    "orientacoes.py","analise_triagem.py","relatorio.py","dashboard.py",
    "agenda.py","configuracoes.py",
]

SUSPECT_CHARS = set("\u017d\u017e\u0161\u0153\u201e\u201c\u2018"
                    "\u00a2\u00b6\u00a4\u00a5\u00bd\u00b7\u2022"
                    "\u203a\u00ae\u2030\u20ac\u25cf\u2122"
                    "\u2014\u201d\u00ab\u00bb\u2033\u2032")

lines_out = []

for fname in FILES:
    fpath = os.path.join(VIEWS_DIR, fname)
    if not os.path.exists(fpath):
        continue
    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
        file_lines = f.readlines()

    for i, line in enumerate(file_lines, 1):
        suspects_in_line = [(j, c) for j, c in enumerate(line) if c in SUSPECT_CHARS]
        if not suspects_in_line:
            continue
        # Build profile
        parts = []
        for j, c in suspects_in_line:
            # Show byte offset and context
            start = max(0, j - 8)
            end = min(len(line), j + 8)
            ctx = line[start:end]
            parts.append("  pos={} cp={:04x} char={} ctx={}".format(
                j, ord(c), repr(c), repr(ctx.strip())))
        lines_out.append("=== {}:{} ===".format(fname, i))
        lines_out.append("  line: {}".format(repr(line.strip()[:120])))
        lines_out.extend(parts)
        lines_out.append("")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines_out))
    
print("Done:", OUT, "total:", len(lines_out))
