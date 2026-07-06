# -*- coding: utf-8 -*-
"""
Verificação final simples e direta.
"""
from pathlib import Path

ROOT = Path(r"C:\Users\58023826\Desktop\react\tkinter\desktop_serpleno\src\ser_pleno")

files = list(ROOT.rglob("*.py"))
bad = []
for path in files:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        bad.append((str(path.relative_to(ROOT)), f"UTF-8 DECODE ERROR: {e}"))
        continue
    
    # Verifica U+FFFD (replacement character)
    if "\ufffd" in text:
        count = text.count("\ufffd")
        bad.append((str(path.relative_to(ROOT)), f"U+FFFD x{count}"))
    
    # Verifica caracteres de controle (exceto \t\n\r)
    controls = [c for c in text if ord(c) < 32 and c not in "\t\n\r"]
    if controls:
        bad.append((str(path.relative_to(ROOT)), f"control chars: {[hex(ord(c)) for c in controls]}"))

print(f"Arquivos com problemas: {len(bad)}")
for rel, problem in bad:
    print(f"  {rel}: {problem}")
if not bad:
    print("✓ Nenhum problema encontrado! Todos os arquivos estão limpos.")
