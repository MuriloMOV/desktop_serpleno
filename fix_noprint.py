# -*- coding: latin-1 -*-
"""
fix_final_noprint.py
Corrige caracteres corrompidos de encoding nos views.
Nenhum print com emoji no stdout; log vai direto para arquivo."""
import os, ast, shutil, sys

sys.stdout.reconfigure(encoding="utf-8")

VIEWS_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\src\ser_pleno\presentation\views"
BACKUP_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\.backup_views_encoding_fix"
LOG = r"F:\Projetos\mobile-web-desk\desktop_serpleno\fix_log_noprint.txt"

FILES = [
    "comunicacao_interna.py","bem_estar.py","estudantes.py","quadro_avisos.py",
    "orientacoes.py","analise_triagem.py","relatorio.py","dashboard.py",
    "agenda.py","configuracoes.py",
]

MAPPINGS = [
    # ── grinning_face U+1F600 prefix corrompeu bytes de outros emojis ─────────
    ([0x1F600, 0x2013, 0x00BC], [0x1F4C1]),  # 😀¼  -> 📁
    ([0x1F600, 0x017D, 0x00A5], [0x1F3A5]),  # 😀Z¥ -> 🎥
    ([0x1F600, 0x017D, 0x00B5], [0x1F3B5]),  # 😀Zµ -> 🎵
    ([0x1F600, 0x2014, 0x0153], [0x1F5DC]),  # 😀—œ -> 🗜
    ([0x1F600, 0x2018],         [0x1F441]),  # 😀'  -> 👁
    ([0x1F600, 0x2018, 0x00A4], [0x1F464]),  # 😀'¤ -> 👤
    ([0x1F600, 0x201D],         [0x1F50D]),  # 😀"  -> 🔍
    ([0x1F600, 0x201D, 0x2014], [0x1F5FA, 0xFE0F]),  # 😀"— -> 🗺
    ([0x1F600, 0x203A, 0x00A1], [0x1F600]),  # 😀›¡ -> 😀
    ([0x1F600, 0x0161, 0x00A8], [0x1F600]),  # 😀š¨ -> 😀
    ([0x1F600, 0x00B7],         [0x1F4CC]),  # 😀·  -> 📌
    ([0x1F600, 0x201C],         [0x1F4CA]),  # 😀“  -> 📊
    # ── 📊 chart U+1F4CA prefix ─────────────────────────────────────────────
    ([0x1F4CA, 0x0161],   [0x1F4CA]),   # 📊Š -> 📊
    ([0x1F4CA, 0x00BD],   [0x1F4CA]),   # 📊½ -> 📊
    ([0x1F4CA, 0x00B7],   [0x1F4CE]),   # 📊· -> 📎
    ([0x1F4CA, 0x017E],   [0x1F4C4]),   # 📊ž -> 📄
    ([0x1F4CA, 0x201C],   [0x1F4CA]),   # 📊“ -> 📊
    ([0x1F4CA, 0x201E],   [0x1F4C4]),   # 📊„ -> 📄
    ([0x1F4CA, 0x00A5],   [0x1F4E5]),   # 📊¥ -> 📥
    ([0x1F4CA, 0x00A5],   [0x1F4E5]),   # 📊¥ -> 📥 (duplicate guard)
    # ── 👁 eye U+1F441 prefix ────────────────────────────────────────────────
    ([0x1F441, 0x00BB],   [0x1F4BB]),  # 👁» -> 💻
    # ── sad_face U+1F61F prefix ──────────────────────────────────────────────
    ([0x1F61F, 0x00A2],   [0x1F61F]),  # 😟¢ -> 😟
    ([0x1F61F, 0x2022],   [0x1F61F]),  # 😟• -> 😟
    ([0x1F61F, 0x0160],   [0x1F600]),  # 😟Š -> 😀
    # ── outras sequências ───────────────────────────────────────────────────
    ([0x25CF, 0x20AC],    [0x25C0]),   # ●€ -> ◀
    ([0x2013, 0x00B6],    [0x25B6]),   # –¶ -> ▶
    ([0x26A1, 0x2122],    [0x2699, 0xFE0F]),  # ⚡™ -> ⚙️
    ([0x00E2, 0x00A7, 0x2030], [0x1F5C2]),  # â§‰ -> 🗂
    ([0x00E2, 0x00B3],    [0x23F3]),  # â³ -> ⏳
    ([0x00E2, 0x0161, 0x017E], [0x1F5C2]),  # âŠž -> 🗂
    ([0x00E2, 0x2020, 0x2032], [0x2B06, 0xFE0F]),  # â†↑ -> ⬆️
    ([0x00E2, 0x2020, 0x2033], [0x2B07, 0xFE0F]),  # â†" -> ⬇️
    ([0x2014, 0x00A2],    [0x2014]),  # —¢ -> —
]

EXTRA_REPL = {
    "A  esquerda": "\u00e0 esquerda",
    "A  direita":  "\u00e0 direita",
}

def u(*cps):
    return "".join(chr(cp) for cp in cps)

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
    log_lines = []
    total = 0

    for fname in FILES:
        fpath = os.path.join(VIEWS_DIR, fname)
        if not os.path.exists(fpath):
            log_lines.append("[SKIP] {} -- not found\n".format(fname))
            continue

        ok_before, _ = check_syntax(fpath)

        # Ler como latin-1 para preservar bytes crus
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

        for old_s, new_s in EXTRA_REPL.items():
            count = content.count(old_s)
            if count:
                content = content.replace(old_s, new_s)
                n_changes += count

        if content != original:
            shutil.copy2(fpath, os.path.join(BACKUP_DIR, fname))
            # Escrever como utf-8
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            ok_after, err_after = check_syntax(fpath)
            status = "syntax OK" if ok_after else "SYNTAX ERR " + err_after
            log_lines.append("[FIXED] {} -- {:3d} | {}\n".format(fname, n_changes, status))
            log_lines.extend(["       " + d + "\n" for d in details])
        else:
            syn = "syntax OK" if ok_before else "syntax BROKEN"
            log_lines.append("[OK] {} -- 0 | {}\n".format(fname, syn))

        total += n_changes

    with open(LOG, "w", encoding="utf-8") as f:
        f.write("FIX LOG {}\n".format(
            __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write("="*60 + "\n\n")
        f.writelines(log_lines)
        f.write("\nTotal: {}\nBackups: {}\n".format(total, BACKUP_DIR))

main()
