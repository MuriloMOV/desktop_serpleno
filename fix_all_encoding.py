# -*- coding: latin-1 -*-
"""
fix_all_encoding.py - Corrige TODOS os caracteres corrompidos de encoding.
Todos os mapeamentos sao baseados nos hex bytes REAIS dos arquivos.

Passo 1: ler arquivo em modo binario, decodificar como latin-1 (1:1 byte->cp)
Passo 2: aplicar substituicoes literais das sequencias corrompidas
Passo 3: re-escrever como utf-8
"""
import os, ast, shutil

VIEWS_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\src\ser_pleno\presentation\views"
BACKUP_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\.backup_views_encoding_fix"
LOG = r"F:\Projetos\mobile-web-desk\desktop_serpleno\fix_all_log.txt"

FILES = [
    "comunicacao_interna.py","bem_estar.py","estudantes.py","quadro_avisos.py",
    "orientacoes.py","analise_triagem.py","relatorio.py","dashboard.py",
    "agenda.py","configuracoes.py",
]

def u(*cps):
    return "".join(chr(cp) for cp in cps)

# MAPPINGS: (src_cps, dst_cps, note)
# src_cps = codepoints da sequencia CORROMPIDA (conforme bytes reais no arquivo)
# dst_cps = codepoints da substituicao CORRETA
MAPPINGS = [
    # ── PREFIXO: grinning_face U+1F600 (😀) ────────────────────────────────────
    # Usado em: comunicacao_interna.py, quadro_avisos.py, orientacoes.py
    # Caminho: f0 9f 98 80 = 😀 em bytes UTF-8
    # 😀 + en-dash + one_quarter = file folder 📁 (U+1F4C1) ??  no, ver bytes
    # Bytes reais: f0 9f 98 80 e2 80 93 c2 bc -> 😀 + en dash + ¼
    # Mas o INTENDIDO era: 📁 (U+1F4C1 = f0 9f 93 81)
    # A corrupcao: o que era originalmente 📁 (f0 9f 93 81) foi
    # re-interpretado em latin-1: 0xf0 0x9f 0x93 0x81 -> caractere invalido
    # Depois re-escrito como UTF-8 VAZIO + 0x93 0x81 -> não forma 🗁
    # O que realmente aparece no arquivo: 😀–¼ (U+1F600 U+2013 U+00BC)

    # comunicacao_interna.py — icon definitions
    ([0x1F600, 0x2013, 0x00BC], [0x1F4C1]),   # 😀¼ -> 📁 pasta   (f0 9f 98 80 e2 80 93 c2 bc)
    ([0x1F600, 0x017D, 0x00A5], [0x1F3A5]),   # 😀Z¥ -> 🎥        (f0 9f 98 80 c5 a0 c2 a5)
    ([0x1F600, 0x017D, 0x00B5], [0x1F3B5]),   # 😀Zµ -> 🎵        (f0 9f 98 80 c5 a0 c2 b5)
    ([0x1F600, 0x2014, 0x0153], [0x1F5DC]),   # 😀—œ -> 🗜        (f0 9f 98 80 e2 80 94 c5 93)
    # comunicacao_interna.py + orientacoes.py — emoji_icons
    ([0x1F600, 0x2018],         [0x1F441]),   # 😀'  -> 👁 view    (f0 9f 98 80 e2 80 98)
    ([0x1F600, 0x2018, 0x00A4], [0x1F464]),   # 😀'¤ -> 👤 person  (f0 9f 98 80 e2 80 98 c2 a4) [estudantes]
    ([0x1F600, 0x201D],         [0x1F50D]),   # 😀"  -> 🔍 search  (f0 9f 98 80 e2 80 9d)
    ([0x1F600, 0x203A, 0x00A1], [0x1F600]),   # 😀›¡ -> 😀         (f0 9f 98 80 e2 80 ba c2 a1)
    ([0x1F600, 0x0161, 0x00A8], [0x1F600]),   # 😀š¨ -> 😀        (f0 9f 98 80 c5 a1 c2 a8)
    # orientacoes.py — buttons
    ([0x1F600, 0x201D, 0x2014], [0x1F5FA, 0xFE0F]),  # 😀"— -> 🗺 (f0 9f 98 80 e2 80 9d e2 80 94)

    # ── PREFIXO: 📊 chart U+1F4CA + LATIN-1 suffix ────────────────────────────
    # Bytes: f0 9f 93 8a + byte (latin-1 suffix byte)
    ([0x1F4CA, 0x0161],   [0x1F4CA]),  # 📊Š    -> 📊  (f0 9f 93 8a c5 a1)
    ([0x1F4CA, 0x00BD],   [0x1F4CA]),  # 📊½    -> 📊  (f0 9f 93 8a c2 bd)
    ([0x1F4CA, 0x00B7],   [0x1F4CE]),  # 📊·    -> 📎  (f0 9f 93 8a c2 b7)
    ([0x1F4CA, 0x017E],   [0x1F4C4]),  # 📊ž    -> 📄  (f0 9f 93 8a c5 be)
    ([0x1F4CA, 0x201C],   [0x1F4CA]),  # 📊"    -> 📊  (f0 9f 93 8a e2 80 9c) -- quando usado local p/ chart
    ([0x1F4CA, 0x201E],   [0x1F4C4]),  # 📊„    -> 📄  (f0 9f 93 8a e2 80 9e)
    ([0x1F4CA, 0x00A5],   [0x1F4E5]),  # 📊¥    -> 📥  (f0 9f 93 8a c2 a5)
    # quadrantes avisos footer
    ([0x1F4CA, 0x00B7],   [0x1F4CC]),  # 📊·    -> 📌  pin (f0 9f 93 8a c2 b7, context card_avisos)

    # ── PREFIXO: 👁 eye U+1F441 + LATIN-1 suffix ──────────────────────────────
    # Bytes: f0 9f 91 81 + byte
    ([0x1F441, 0x00BB],   [0x1F4BB]),  # 👁»    -> 💻  (f0 9f 91 81 c2 bb)

    # ── PREFIXO: 💙 blue_heart U+1F499 + LATIN-1 suffix ──────────────────────
    # (se aparecer em bem_estar)
    ([0x1F499, 0x0160],   [0x1F499]),  # 💙Š    -> 💙  (f0 9f 92 99 c5 a0)

    # ── SEQUENCIAS MISTAS (nao tem emoji prefixo) ─────────────────────────────
    # agenda.py — navegacao botoes
    ([0x25CF, 0x20AC],    [0x25C0]),   # ●€ -> ◀  (e2 97 8f e2 82 ac)
    ([0x2013, 0x00B6],    [0x25B6]),   # –¶ -> ▶  (e2 80 93 c2 b6)
    # agenda.py icon
    ([0x26A1, 0x2122],    [0x2699, 0xFE0F]),  # ⚡™ -> ⚙️ (e2 9a a1 e2 84 a2)
    # quadro_avisos — layout label
    ([0x00E2, 0x0161, 0x017E], [0x1F5C2]),  # âŠž -> 🗂 (c3 a2 c5 a0 c5 be)
    # quadro_avisos — botoes up/down
    ([0x00E2, 0x2020, 0x2032], [0x2B06, 0xFE0F]),  # â†' -> ⬆️ (c3 a2 e2 88 b0)
    ([0x00E2, 0x2020, 0x2033], [0x2B07, 0xFE0F]),  # â†" -> ⬇️ (c3 a2 e2 88 b1)
    # quadro_avisos / analise triagem — loading
    ([0x00E2, 0x00B3],    [0x23F3]),  # â³ -> ⏳ (c3 a2 c2 b3)
    # orientacoes — duplicar button
    ([0x00E2, 0x00A7, 0x2030], [0x1F5C2]),  # â§‰ -> 🗂 (c3 a2 c2 a7 e2 80 b0)
    # configuracoes — em-dash quebrado
    ([0x2014, 0x00A2],    [0x2014]),  # —¢ -> —  (e2 80 94 c2 a2)
    # quadro_avisos — footer icon
    ([0x1F91, 0x00A4],    [0x1F464]),  # 👤 (f0 9f 91 81 c2 a4) -- eye+nobreak = person
]

# EXTRA: fixes de texto (typo A preposicao)
EXTRA_REPLACEMENTS = {
    "A  esquerda": "\u00e0 esquerda",   # -> à esquerda
    "A  direita":  "\u00e0 direita",    # -> à direita
}

def check_syntax(fpath):
    try:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            ast.parse(f.read())
        return True, "OK"
    except SyntaxError as e:
        return False, "linha " + str(e.lineno) + ": " + e.msg
    except Exception as e:
        return False, str(e)

def main():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    log_lines = []
    total = 0

    for fname in FILES:
        fpath = os.path.join(VIEWS_DIR, fname)
        if not os.path.exists(fpath):
            log_lines.append("[SKIP] {} -- not found\n".format(fname))
            continue

        ok_before, err_before = check_syntax(fpath)

        # Leitura como latin-1 preserva bytes originais como codepoints
        with open(fpath, "r", encoding="latin-1") as f:
            content = f.read()

        original = content
        n_changes = 0
        details = []

        for src_cps, dst_cps in MAPPINGS:
            old = u(*src_cps)
            new = u(*dst_cps)
            count = content.count(old)
            if count:
                content = content.replace(old, new)
                n_changes += count
                details.append("  {:3d}x  [{}] -> [{}]".format(
                    count,
                    ":".join("{:04x}".format(c) for c in src_cps),
                    ":".join("{:04x}".format(c) for c in dst_cps),
                ))

        for old_str, new_str in EXTRA_REPLACEMENTS.items():
            count = content.count(old_str)
            if count:
                content = content.replace(old_str, new_str)
                n_changes += count

        if content != original:
            shutil.copy2(fpath, os.path.join(BACKUP_DIR, fname))
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            ok_after, err_after = check_syntax(fpath)
            status = ("syntax OK" if ok_after else "SYNTAX ERR " + err_after)
            log_lines.append("[FIXED] {} -- {:3d} changes | {}\n".format(
                fname, n_changes, status))
            log_lines.extend(["       " + d + "\n" for d in details])
        else:
            syn = "syntax OK" if ok_before else "syntax BROKEN"
            log_lines.append("[OK]    {} -- 0 | {}\n".format(fname, syn))

        total += n_changes

    with open(LOG, "w", encoding="utf-8") as f:
        f.write("FIX LOG {}\n".format(
            __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write("=" * 60 + "\n\n")
        f.writelines(log_lines)
        f.write("\nTotal: {}\n".format(total))

main()
