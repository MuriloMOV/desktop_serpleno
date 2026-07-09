# -*- coding: utf-8 -*-
"""detect_corruption.py — Detecta caracteres corrompidos nos arquivos de view."""
import os

VIEWS_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\src\ser_pleno\presentation\views"
OUT = r"F:\Projetos\mobile-web-desk\desktop_serpleno\corruption_report.txt"

FILES = [
    "comunicacao_interna.py","bem_estar.py","estudantes.py","quadro_avisos.py",
    "orientacoes.py","analise_triagem.py","relatorio.py","dashboard.py",
    "agenda.py","configuracoes.py",
]

lines_out = []
for fname in FILES:
    fpath = os.path.join(VIEWS_DIR, fname)
    if not os.path.exists(fpath):
        continue
    with open(fpath, "rb") as f:
        raw = f.read()
    content = raw.decode("utf-8", errors="replace")
    file_lines = content.split("\n")
    for i, line in enumerate(file_lines, 1):
        if any(c in line for c in "\u017d\u0161\u0153\u201e\u201d\u201c\u2018"
                                  "\u00a2\u00b6\u00a4\u00a5\u00bd\u00b7\u2022"
                                  "\u203a\u00ae\u2030\u2032\u2033\u20ac\u25cf"
                                  "\u2122\u017e\u2014"):
            # Find specifically the corrupted patterns
            lines_out.append("{}:{} | {}".format(fname, i, repr(line.strip()[:150])))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines_out))
    f.write("\n\nTotal linhas com caracteres corrompidos: {}\n".format(len(lines_out)))

print("Report saved to:", OUT)
print("Total lines with corruption:", len(lines_out))
