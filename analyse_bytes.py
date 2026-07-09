# -*- coding: latin-1 -*-
"""
analyse_bytes.py — Le arquivos em modo binario/latin-1 para mapear bytes exatos
dos caracteres corrompidos.
"""
import os

VIEWS_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\src\ser_pleno\presentation\views"
OUT = r"F:\Projetos\mobile-web-desk\desktop_serpleno\raw_bytes_report.txt"

FILES = [
    "comunicacao_interna.py","bem_estar.py","estudantes.py","quadro_avisos.py",
    "orientacoes.py","analise_triagem.py","relatorio.py","dashboard.py",
    "agenda.py","configuracoes.py",
]

# Palavras/patterns suspeitos para buscar no raw
SUSPECT_PATTERNS = [
    "Imagens", "Videos", "Audio", "Planilhas", "Presenta", "Arquivos Zip", "Code",
    "Categoria", "Autor", "Layout", "Horario", "Carregando",
    "Humor", "Criticos", "Bom", "Baixo", "Risco",
    "Idade", "Nome Completo", "Email",
    "Duplicar", "Excluir", "Tema", "Encaminhamento",
    "Exportacao", "Baixar", "Visualizar",
    "Dispositivo", "Gerenciar",
    "busca", "search",
]

lines_out = []

for fname in FILES:
    fpath = os.path.join(VIEWS_DIR, fname)
    if not os.path.exists(fpath):
        continue
    with open(fpath, "rb") as f:
        raw = f.read()
    # Decode as latin-1 (1:1 byte->codepoint) to preserve exact bytes
    content_latin1 = raw.decode("latin-1")
    file_lines = content_latin1.split("\n")
    for i, line in enumerate(file_lines, 1):
        stripped = line.strip()
        # Find lines containing our suspect patterns
        for pat in SUSPECT_PATTERNS:
            if pat.lower() in stripped.lower():
                # Show hex for first 80 chars
                hex_repr = " ".join("{:02x}".format(b) for b in raw[
                    sum(len(l)+1 for l in file_lines[:i-1]):
                    sum(len(l)+1 for l in file_lines[:i])
                ][:80])
                lines_out.append("{}:{} [{}]".format(fname, i, hex_repr))
                break  # one entry per line

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines_out))

print("Done. Report:", OUT)
print("Total lines found:", len(lines_out))
