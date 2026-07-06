# -*- coding: utf-8 -*-
"""
Verificação final: busca caracteres suspeitos em src/ser_pleno/**/*.py
"""
from pathlib import Path
import re

ROOT = Path(r"C:\Users\58023826\Desktop\react\tkinter\desktop_serpleno\src\ser_pleno")

# Caracteres suspeitos: controles, replacement, mojibake comum
SUSPECT = re.compile(
    r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]'  # controles
    r'|�'  # U+FFFD replacement
    r'|â[•–—”‚œ˜¦”¬´¨¼½¾¿]'  # mojibake bullet/dash
    r'|â€[œ˜¦”]'  # mojibake smart quotes
    r'|â„[¢£¤¥¦§¨©ª«¬­®¯]'  # mojibake special
    r'|Â[©®±ºª]'  # mojibake symbols
    r'|Ã[§£¥¦§¨©ª«¬­®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ]'  # mojibake accents
)

files = list(ROOT.rglob("*.py"))
bad = []
for path in files:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        bad.append((str(path.relative_to(ROOT)), "INVALID UTF-8"))
        continue
    
    matches = SUSPECT.findall(text)
    if matches:
        bad.append((str(path.relative_to(ROOT)), matches))

print(f"Arquivos com caracteres suspeitos: {len(bad)}")
for rel, matches in bad:
    print(f"  {rel}: {matches}")
if not bad:
    print("✓ Nenhum caractere suspeito encontrado!")
