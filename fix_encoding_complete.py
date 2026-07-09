# -*- coding: latin-1 -*-
"""
fix_encoding_complete.py - Corrige TODOS os caracteres corrompidos de encoding.
Estrategia: leitura binaria, decodificacao como latin-1 (1:1 byte->cp), 
            substituicao, re-escrita como utf-8.
"""
import os, ast, shutil
from datetime import datetime

VIEWS_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\src\ser_pleno\presentation\views"
BACKUP_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\.backup_views_encoding_fix"
LOG = r"F:\Projetos\mobile-web-desk\desktop_serpleno\fix_log_complete.txt"

FILES = [
    "comunicacao_interna.py","bem_estar.py","estudantes.py","quadro_avisos.py",
    "orientacoes.py","analise_triagem.py","relatorio.py","dashboard.py",
    "agenda.py","configuracoes.py",
]

def u(*cps):
    return "".join(chr(cp) for cp in cps)

def hex_repr(s, maxlen=8):
    return ":".join("{:04x}".format(ord(c)) for c in s[:maxlen])

# MAPPINGS: (src_cps, dst_cps)
MAPPINGS = [
    # PASS 1: grinning_face U+1F600 prefix
    ([0x1F600, 0x2013, 0x00BC], [0x1F4C1]),  # 😀¼ -> folder
    ([0x1F600, 0x017D, 0x00A5], [0x1F3A5]),  # 😀Z¥ -> video
    ([0x1F600, 0x017D, 0x00B5], [0x1F3B5]),  # 😀Zµ -> music
    ([0x1F600, 0x2014, 0x0153], [0x1F5DC]),  # 😀—œ -> zip
    ([0x1F600, 0x2018],         [0x1F441]),  # 😀'  -> eye
    ([0x1F600, 0x2018, 0x00A4], [0x1F464]),  # 😀'¤ -> person
    ([0x1F600, 0x201D],         [0x1F50D]),  # 😀"  -> search
    ([0x1F600, 0x201D, 0x2014], [0x1F5FA, 0xFE0F]),  # 😀"— -> map
    ([0x1F600, 0x203A, 0x00A1], [0x1F600]),  # 😀›¡ -> smiley
    ([0x1F600, 0x0161, 0x00A8], [0x1F600]),  # 😀š¨ -> smiley
    ([0x1F600, 0x00B7],         [0x1F4CC]),  # 😀·  -> pin
    ([0x1F600, 0x201C],         [0x1F4CA]),  # 😀"  -> chart fallback

    # PASS 2: 📊 chart prefix U+1F4CA + corrupted suffix
    ([0x1F4CA, 0x0161],   [0x1F4CA]),   # 📊Š -> 📊
    ([0x1F4CA, 0x00BD],   [0x1F4CA]),   # 📊½ -> 📊
    ([0x1F4CA, 0x00B7],   [0x1F4CE]),   # 📊· -> 📎
    ([0x1F4CA, 0x017E],   [0x1F4C4]),   # 📊ž -> 📄
    ([0x1F4CA, 0x201C],   [0x1F4CA]),   # 📊“ -> 📊
    ([0x1F4CA, 0x201E],   [0x1F4C4]),   # 📊„ -> 📄
    ([0x1F4CA, 0x00A5],   [0x1F4E5]),   # 📊¥ -> 📥
    ([0x1F4CA, 0x201C],   [0x1F4CA]),   # 📊"  -> 📊 (duplicate guard)

    # PASS 3: 👁 eye prefix U+1F441 + corrupted suffix
    ([0x1F441, 0x00BB],   [0x1F4BB]),  # 👁» -> 💻

    # PASS 4: Symbol-only corruptions
    ([0x25CF, 0x20AC],    [0x25C0]),   # ●€ -> ◀
    ([0x2013, 0x00B6],    [0x25B6]),   # –¶ -> ▶
    ([0x26A1, 0x2122],    [0x2699, 0xFE0F]),  # ⚡™ -> ⚙️
    ([0x00E2, 0x00A7, 0x2030], [0x1F5C2]),  # â§‰ -> 🗂
    ([0x00E2, 0x00B3],    [0x23F3]),   # â³ -> ⏳
    ([0x00E2, 0x0161, 0x017E], [0x1F5C2]),  # âŠž -> 🗂
    ([0x00E2, 0x2020, 0x2032], [0x2B06, 0xFE0F]),  # â†↑ -> ⬆️
    ([0x00E2, 0x2020, 0x2033], [0x2B07, 0xFE0F]),  # â†" -> ⬇️

    # PASS 5: sadd_face U+1F61F prefix
    ([0x1F61F, 0x00A2],  [0x1F61F]),  # 😟¢ -> 😟
    ([0x1F61F, 0x2022],  [0x1F61F]),  # 😟• -> 😟
    ([0x1F61F, 0x0160],  [0x1F600]),  # 😟Š -> 😀

    # PASS 6: Other emoji prefixes
    ([0x1F600, 0x017D, 0x201A], [0x1F382]),  # 😀Ž‚ -> 🎂
    ([0x203A, 0x00AE],    [0x1F4E4]),   # ‹®  -> 📤
    ([0x1F4CA, 0x00B7],   [0x1F4CE]),   # 📊·  -> 📎 duplicate -> use best match
]

# Resolve duplicates by keeping the first mapping
seen_src = {}
final_mappings = []
for m in MAPPINGS:
    src_key = tuple(m[0])
    if src_key not in seen_src:
        seen_src[src_key] = m
        final_mappings.append(m)

EXTRA_REPLACEMENTS = {
    "A  esquerda": "\u00e0 esquerda",
    "A  direita":  "\u00e0 direita",
}

def check_syntax(fpath):
    try:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            ast.parse(f.read())
        return True, "OK"
    except SyntaxError as e:
        return False, "linha {}".format(e.lineno) + ": " + e.msg
    except Exception as e:
        return False, str(e)

def main():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    log_lines = []
    total_changes = 0

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
        details = []

        for src_cps, dst_cps in final_mappings:
            old = u(*src_cps)
            new = u(*dst_cps)
            count = content.count(old)
            if count:
                content = content.replace(old, new)
                changes += count
                details.append("  {:3d}x  {} -> {}".format(
                    count,
                    hex_repr(old),
                    hex_repr(new),
                ))

        for old_str, new_str in EXTRA_REPLACEMENTS.items():
            count = content.count(old_str)
            if count:
                content = content.replace(old_str, new_str)
                changes += count

        if content != original:
            shutil.copy2(fpath, os.path.join(BACKUP_DIR, fname))
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            ok_after, err_after = check_syntax(fpath)
            status = ("syntax OK" if ok_after else
                      "SYNTAX ERR " + err_after)
            log_lines.append("[FIXED] {} -- {:3d} changes | {}\n".format(
                fname, changes, status))
            log_lines.extend(["       " + d + "\n" for d in details])
        else:
            syn = "syntax OK" if ok_before else "syntax BROKEN"
            log_lines.append("[OK]    {} -- 0 | {}\n".format(fname, syn))

        total_changes += changes

    with open(LOG, "w", encoding="utf-8") as f:
        f.write("FIX LOG {}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write("=" * 60 + "\n\n")
        f.writelines(log_lines)
        f.write("\nTotal: {}\nBackups: {}\n".format(total_changes, BACKUP_DIR))

main()
