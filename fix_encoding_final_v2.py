# -*- coding: latin-1 -*-
"""
fix_encoding_final_v2.py
Replaces corrupted multibyte UTF-8 sequences in view files.
All mappings use Python unicode escapes only to avoid source-encoding issues.
"""
import os, ast, shutil
from datetime import datetime

VIEWS_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\src\ser_pleno\presentation\views"
BACKUP_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\.backup_views_encoding_fix"
LOG = r"F:\Projetos\mobile-web-desk\desktop_serpleno\fix_log_final2.txt"

FILES = [
    "comunicacao_interna.py","bem_estar.py","estudantes.py","quadro_avisos.py",
    "orientacoes.py","analise_triagem.py","relatorio.py","dashboard.py",
    "agenda.py","configuracoes.py",
]

# Helper: build a unicode string from a list of codepoints
def u(*cps):
    return "".join(chr(cp) for cp in cps)

# ── Mapeamento de sequencias corrompidas -> corretas ─────────────────────────
# Keys are unicode strings built from ordinal codepoints
REPLACEMENTS = {}

# Build from codepoint tuples: (corrupt_seq_cps..., correct_seq_cps...)
MAPPINGS = [
    # ── comunicacao_interna.py ───────────────────────────────────────────────
    # prefixo emoji grinning face U+1F600 + en_dash U+2013 + vulgar_fraction_one_quarter U+00BC
    ([0x1F600, 0x2013, 0x00BC], [0x1F4C1]),     # 😀–¼ -> 📁 folder
    ([0x1F600, 0x017D, 0x00A5], [0x1F3A5]),    # 😀Ž¥ -> 🎥 camera  (Z-with-caron + yen)
    ([0x1F600, 0x017D, 0x00B5], [0x1F3B5]),    # 😀Žµ -> 🎵 music   (micro sign)
    ([0x1F600, 0x2014, 0x0153], [0x1F5DC]),    # 😀—œ -> 🗜 zip    (em-dash + oe ligature)
    # prefixo grinning face + left_single_quot_mark U+2018
    ([0x1F600, 0x2018],          [0x1F441]),    # 😀'  -> 👁 view
    # prefixo grinning face + right_dbl_quot_mark U+201D
    ([0x1F600, 0x201D],          [0x1F50D]),    # 😀"  -> 🔍 search
    # grinning face + dbl_quot + em-dash  (orientacoes)
    ([0x1F600, 0x201D, 0x2014],  [0x1F5FA, 0xFE0F]),  # 😀"— -> 🗺
    # grinning face + right_pt_quot_mark U+203A + inverted_excl U+00A1
    ([0x1F600, 0x203A, 0x00A1],  [0x1F600]),    # 😀›¡ -> 😀
    # grinning face + s_caron U+0161 + diaeresis U+00A8
    ([0x1F600, 0x0161, 0x00A8],  [0x1F600]),    # 😀š¨ -> 😀

    # ── bem_estar.py ─────────────────────────────────────────────────────────
    # sad emoji U+1F61F + cent U+00A2
    ([0x1F61F, 0x00A2],  [0x1F61F]),             # 😟¢ -> 😟
    # sad + bullet U+2022
    ([0x1F61F, 0x2022],  [0x1F61F]),             # 😟• -> 😟
    # sad + s_caron U+0160
    ([0x1F61F, 0x0160],  [0x1F600]),             # 😟Š -> 😀

    # ── estudantes.py ────────────────────────────────────────────────────────
    # grinning face + Z-caron U+017D + low_rev_quot U+201A
    ([0x1F600, 0x017D, 0x201A], [0x1F382]),      # 😀Ž‚ -> 🎂
    # grinning face + left_single_quot + currency U+00A4
    ([0x1F600, 0x2018, 0x00A4], [0x1F464]),      # 😀‘¤ -> 👤

    # ── quadro_avisos.py ─────────────────────────────────────────────────────
    # grinning face + middle_dot U+00B7
    ([0x1F600, 0x00B7],   [0x1F4CC]),            # 😀· -> 📌
    # U+1F4CA (chart) + "Local" lookahead context - use combined string
    # Note: handled separately via direct string

    # ── orientacoes.py ───────────────────────────────────────────────────────
    # U+00E2 U+00A7 U+2030 -> 🗂
    ([0x00E2, 0x00A7, 0x2030], [0x1F5C2]),      # â§‰ -> 🗂

    # ── analise_triagem.py ───────────────────────────────────────────────────
    # U+00E2 U+00B3 -> ⏳ (hourglass)
    ([0x00E2, 0x00B3],    [0x23F3]),             # â³ -> ⏳

    # ── relatorio.py ─────────────────────────────────────────────────────────
    # U+1F4CA (chart) + yen symbol U+00A5 -> 📥 download arrow
    ([0x1F4CA, 0x00A5],   [0x1F4E5]),            # 📊¥ -> 📥

    # ── agenda.py ────────────────────────────────────────────────────────────
    # U+25CF (bullet) + U+20AC (euro) -> ◀
    ([0x25CF, 0x20AC],    [0x25C0]),             # ●€ -> ◀
    # U+2013 (en-dash) + U+00B6 (pilcrow) -> ▶
    ([0x2013, 0x00B6],    [0x25B6]),             # –¶ -> ▶
    # U+26A1 (lightning) + U+2122 (TM) -> ⚙
    ([0x26A1, 0x2122],    [0x2699, 0xFE0F]),    # ⚡™ -> ⚙️

    # ── configuracoes.py ─────────────────────────────────────────────────────
    # em-dash U+2014 + cent U+00A2 -> em-dash plain
    ([0x2014, 0x00A2],    [0x2014]),             # —¢ -> —

    # ── Global icon-prefix combos (shared across files) ───────────────────────
    # 📁 emoji sequences (prefix part already correct, fix suffix)
    # U+1F4CA chart + caron-S U+0161 -> strip to plain 📊
    ([0x1F4CA, 0x0161],   [0x1F4CA]),            # 📊Š -> 📊
    # chart + vulgar_one_half U+00BD -> strip
    ([0x1F4CA, 0x00BD],   [0x1F4CA]),            # 📊½ -> 📊
    # chart + middle_dot U+00B7 -> paperclip 📎
    ([0x1F4CA, 0x00B7],   [0x1F4CE]),            # 📊· -> 📎
    # chart + z-caron U+017E -> doc 📄
    ([0x1F4CA, 0x017E],   [0x1F4C4]),            # 📊ž -> 📄
    # chart + left_dbl_quot U+201C -> strip to chart 📊
    ([0x1F4CA, 0x201C],   [0x1F4CA]),            # 📊“ -> 📊
    # chart + low_rev_quot U+201E -> doc 📄
    ([0x1F4CA, 0x201E],   [0x1F4C4]),            # 📊„ -> 📄
    # eye + guillemet_right U+00BB -> 💻
    ([0x1F441, 0x00BB],   [0x1F4BB]),            # 👁» -> 💻
    # << angle bracket U+203A + reg TM U+00AE -> send 📤
    ([0x203A, 0x00AE],     [0x1F4E4]),            # ›® or ‹® -> 📤
]

EXTRA_REPLACEMENTS = {
    # quadro_avisos.py - typo from encoding
    "A  esquerda": "\u00e0 esquerda",
    "A  direita":  "\u00e0 direita",
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
    log_lines = []
    total = 0

    for fname in FILES:
        fpath = os.path.join(VIEWS_DIR, fname)
        if not os.path.exists(fpath):
            log_lines.append("[SKIP] {} -- not found\n".format(fname))
            continue

        ok_before, err_before = check_syntax(fpath)

        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        original = content
        changes = 0
        detail = []

        for mapping in MAPPINGS:
            src_cps, dst_cps = mapping
            old = u(*src_cps)
            new = u(*dst_cps)
            count = content.count(old)
            if count:
                content = content.replace(old, new)
                changes += count
                detail.append("  {:3d}x  [{}] -> [{}]".format(
                    count,
                    ":".join("{:04x}".format(c) for c in src_cps),
                    ":".join("{:04x}".format(c) for c in dst_cps),
                ))

        for old, new in EXTRA_REPLACEMENTS.items():
            count = content.count(old)
            if count:
                content = content.replace(old, new)
                changes += count
                detail.append("  {:3d}x  '{}' -> '{}'".format(count, repr(old), repr(new)))

        if content != original:
            shutil.copy2(fpath, os.path.join(BACKUP_DIR, fname))
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            ok_after, err_after = check_syntax(fpath)
            status = "syntax OK" if ok_after else "SYNTAX ERR " + err_after
            log_lines.append("[FIXED] {} -- {:3d} changes | {}\n".format(fname, changes, status))
            log_lines.extend(["       " + d + "\n" for d in detail])
        else:
            syn = "syntax OK" if ok_before else "syntax BROKEN"
            log_lines.append("[OK]    {} -- 0 changes | {}\n".format(fname, syn))

        total += changes

    with open(LOG, "w", encoding="utf-8") as f:
        f.write("FIX LOG {}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write("=" * 60 + "\n\n")
        f.writelines(log_lines)
        f.write("\nTotal: {}\nBackups: {}\n".format(total, BACKUP_DIR))

main()
