# -*- coding: latin-1 -*-
"""
direct_fix.py - aplica correcoes diretamente nos arquivos,
baseado nos achados do char_profile.txt.
Usa conteudo literal dos arquivos (latin-1 read -> str replace -> utf-8 write).
"""
import os, ast, shutil

VIEWS_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\src\ser_pleno\presentation\views"
BACKUP_DIR = r"F:\Projetos\mobile-web-desk\desktop_serpleno\.backup_direct_fix"
LOG = r"F:\Projetos\mobile-web-desk\desktop_serpleno\direct_fix_log.txt"

FILES = [
    "comunicacao_interna.py","bem_estar.py","estudantes.py","quadro_avisos.py",
    "orientacoes.py","analise_triagem.py","relatorio.py","dashboard.py",
    "agenda.py","configuracoes.py",
]

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
            log_lines.append("[SKIP] {}\n".format(fname))
            continue

        ok_before, _ = check_syntax(fpath)
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        original = content
        changes = 0

        # ── FIXES COMUNS ─────────────────────────────────────────────────────
        # 1. Corrupcao generica: em-dash + curly quote em strings/codigo
        #    Quando aparece como placeholder de valor vazio: "—" / "—" / "—"
        #    Manter como ASCII — (em-dash) é suportado, só remover o char extra
        #    Onde NAO faz sentido ter curly quotes em codigo:
        pairs_to_fix = [
            # (emoji_prefix + curly_quote/char) -> icon correto ou em-dash limpo
            # format: 'old_substring', 'new_substring'
        ]

        # 2. Corruptos de commentarios: —" -> — (em todas as linhas)
        # Nao vamos modificar comentarios p/ nao quebrar documentacao
        # Apenas corrigir onde aparece em strings de codigo (literais)

        # 3. Corruptos de icon:
        # Estudantes.py: icon="👁¤"
        if 'icon="\U0001f441\u00a4"' in content:
            content = content.replace('icon="\U0001f441\u00a4"', 'icon="\U0001f464"')
            changes += content.count('icon="\U0001f464"') - original.count('icon="\U0001f464"')
        if 'text="\U0001f441\u00a4"' in content:
            content = content.replace('text="\U0001f441\u00a4"', 'text="\U0001f464"')
            changes += content.count('text="\U0001f464"') - original.count('text="\U0001f464"')

        # 4. Botao circular em dashboard: icon="✖"""  (heavy multiply X + r d q m)
        if 'icon="\u271d\u201d"' in content:
            content = content.replace('icon="\u271d\u201d"', 'icon="\u270f"')
            changes += 1

        if 'text="✖\u201d  Sim"' in content:
            content = content.replace('text="✖\u201d  Sim"', 'text="\u270f  Sim"')
            changes += 1

        if 'text="✖\u201d  Salvar Estudante"' in content:
            content = content.replace('text="✖\u201d  Salvar Estudante"', 'text="\u270f  Salvar Estudante"')
            changes += 1

        if 'text="✖\u201d  Publicar"' in content:
            content = content.replace('text="✖\u201d  Publicar"', 'text="\u270f  Publicar"')
            changes += 1

        if 'text="✖\u201d  Salvar Orientação"' in content:
            content = content.replace('text="✖\u201d  Salvar Orientação"', 'text="\u270f  Salvar Orientação"')
            changes += 1

        if 'text="✖\u201d"  command=salvar' in content:
            content = content.replace('text="✖\u201d"  command=salvar', 'text="\u270f"  command=salvar')
            changes += 1

        if 'actions, text="😀\u2014\u2018  Excluir"' in content:
            content = content.replace('actions, text="😀\u2014\u2018  Excluir"', 'actions, text="\U0001f5d1\ufe0f  Excluir"')
            changes += 1

        # (reuse above for other "" buttons with emoji prefix)
        # comunicacao_interna.py: "✖“✖“"
        if 'text=" ✖\u201c✖\u201c"' in content:
            content = content.replace('text=" ✖\u201c✖\u201c"', 'text=" \u270f\u270f"')
            changes += 1

        # 5. ‹®  (LSAQ + reg) -> 📤
        if '"\u203a\u00ae"' in content:
            content = content.replace('"\u203a\u00ae"', '"\U0001f4e4"')
            changes += content.count('\U0001f4e4') - original.count('\U0001f4e4')

        # 6. âŠž -> 🗂 em quadro_avisos.py (Layout label)
        if '"\u00e2\u0161\u017e  Layout"' in content:
            content = content.replace('"\u00e2\u0161\u017e  Layout"', '"\U0001f5c2  Layout"')
            changes += 1

        # 7. â†‘, â†" em quadro_avisos.py botoes
        if '"\u00e2\u2020\u2032"' in content:
            content = content.replace('"\u00e2\u2020\u2032"', '"\u2b06\ufe0f"')
            changes += 1
        if '"\u00e2\u2020\u2033"' in content:
            content = content.replace('"\u00e2\u2020\u2033"', '"\u2b07\ufe0f"')
            changes += 1

        # 8. ●€  navigation button (prev)
        if '"\u25cf\u20ac"' in content:
            content = content.replace('"\u25cf\u20ac"', '"\u25c0"')
            changes += 1

        # 9. –¶  (pilcrow) -> ▶
        if '"\u2013\u00b6"' in content:
            content = content.replace('"\u2013\u00b6"', '"\u25b6"')
            changes += 1

        # 10. ⚡™ -> ⚙️ (gear)
        if 'icon="\u26a1\u2122"' in content:
            content = content.replace('icon="\u26a1\u2122"', 'icon="\u2699\ufe0f"')
            changes += 1

        # 11. —¢  (cent-invalid em-dash) -> —
        if '\u2014\u00a2' in content:
            content = content.replace('\u2014\u00a2', '\u2014')
            changes += content.count('\u2014') - original.count('\u2014')

        # 12. —" em strings/codigo (onde nao eh commentario deliberado)
        # Apenas substituir em strings onde curly dbl quote apos em-dash é obviamente corrupcao
        # Nao mexer em comments deliberados
        # Padrao: em-dash + l d q m  (—") -> trocar apenas para em-dash ASCII
        if '\u2014\u201c' in content:
            # Substituir em-dash + curly dbl open quote por apenas em-dash
            # Pular linhas de commentário (iniciadas com #)
            new_content = []
            n = 0
            for line in content.split('\n'):
                stripped = line.lstrip()
                if stripped.startswith('#') and '\u2014\u201c' in line:
                    # Only fix if it's clearly a corruption pattern  —"
                    line = line.replace('\u2014\u201c', '\u2014')
                    n += line.count('\u2014') - stripped.count('\u2014')
                elif '\u2014\u201c' in line:
                    line = line.replace('\u2014\u201c', '\u2014')
                    n += 1
                new_content.append(line)
            content = '\n'.join(new_content)
            changes += n

        if content != original:
            shutil.copy2(fpath, os.path.join(BACKUP_DIR, fname))
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            ok_after, err_after = check_syntax(fpath)
            status = "syntax OK" if ok_after else "SYNTAX ERR " + err_after
            log_lines.append("[FIXED] {} -- {} | {}\n".format(fname, changes, status))
        else:
            syn = "syntax OK" if ok_before else "syntax BROKEN"
            log_lines.append("[OK] {} -- 0 | {}\n".format(fname, syn))

        total += changes

    with open(LOG, "w", encoding="utf-8") as f:
        f.write("DIRECT FIX LOG\n" + "="*60 + "\n\n")
        f.writelines(log_lines)
        f.write("\nTotal: {}\n".format(total))

main()
