# -*- coding: utf-8 -*-
"""
Varredura completa de todos os arquivos Python em src/ser_pleno/
e corrige TODOS os caracteres corrompidos (mojibake).
"""
from pathlib import Path

ROOT = Path(r"C:\Users\58023826\Desktop\react\tkinter\desktop_serpleno\src\ser_pleno")

# Mapeamento completo de mojibake -> caractere correto
FIXES = {
    # Box-drawing e bullets (padrão mais recente)
    "â•": "•",
    "â–": "–",
    "â—": "—",
    "â”€": "─",
    "â”‚": "│",
    "â”œ": "├",
    "â”¤": "┤",
    "â”¬": "┬",
    "â”´": "┴",
    "â”¼": "┼",
    "â•©": "►",
    "â•«": "◄",
    # Aspas e pontuação
    "â€œ": "\u201c",
    "â€": "\u201d",
    "â€˜": "\u2018",
    "â€™": "\u2019",
    "â€¦": "…",
    "â€¢": "•",
    "â€“": "–",
    "â€”": "—",
    "â„¢": "™",
    # Marca registrada, copyright
    "Â©": "©",
    "Â®": "®",
    "Â±": "±",
    # Ordinais e feminino
    "Âº": "º",
    "Âª": "ª",
    # Acentos latinos
    "Ã§": "ç",
    "Ã£": "ã",
    "Ã¡": "á",
    "Ã©": "é",
    "Ã³": "ó",
    "Ãº": "ú",
    "Ãª": "ê",
    "Ã˜": "Ø",
    "Ã˜": "Ø",
    "Ã‡": "Ç",
    "Ã‹": "Ë",
    "Ã©": "É",
    "Ãª": "Ê",
    "Ã­": "Í",
    "Ã“": "Ó",
    "Ãš": "Ú",
    "Ã±": "ñ",
    "Ã‘": "Ñ",
    "Ã": "Á",
    "Ã": "Í",
    "Ã": "Ó",
    "Ãš": "Ú",
    "Ã©": "é",
    "Ãª": "ê",
    "Ã§": "ç",
    "Ã£": "ã",
    "Ã¡": "á",
    "Ã³": "ó",
    # Caracteres de controle e outros
    "": "",  # U+0090 DELETE
    "": "",  # U+0091
    "": "",  # U+0092
    "": "",  # U+0093
    "": "",  # U+0094
    "": "",  # Outras variações
}

# Padrões regex para catch-all de mojibake
import re

# Padrão: sequência de â + byte alto/baixo
MJ_PATTERNS = [
    (re.compile(r'â[•–—”‚œ˜¦”¬´¨¼½¾¿]'), "bullet_dash"),
    (re.compile(r'â€[œ˜¦”]'), "smart_quotes"),
    (re.compile(r'â„[¢£¤¥¦§¨©ª«¬­®¯]'), "special"),
    (re.compile(r'Â[©®±ºª]'), "symbols"),
    (re.compile(r'Ã[§£¥¦§¨©ª«¬­®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ]'), "latin1_accents"),
]

files = list(ROOT.rglob("*.py"))
fixed = 0
details = []

for path in files:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        continue
    
    new = text
    count = 0
    fixes_applied = []
    
    # Aplica substituições diretas
    for bad, good in FIXES.items():
        if bad in new:
            new = new.replace(bad, good)
            count += new.count(bad)  # Conta ocorrências
            fixes_applied.append(bad)
    
    # Aplica padrões regex
    for pattern, name in MJ_PATTERNS:
        matches = pattern.findall(new)
        if matches:
            # Substitui cada match pelo caractere correto
            for m in matches:
                # Tenta adivinhar o caractere correto baseado no padrão
                if "â€" in m:
                    replacement = {
                        "â€œ": "\u201c", "â€": "\u201d",
                        "â€˜": "\u2018", "â€™": "\u2019",
                    }.get(m, m)
                elif "â•" in m:
                    replacement = "•"
                elif "â–" in m:
                    replacement = "–"
                elif "â—" in m:
                    replacement = "—"
                else:
                    replacement = m
                new = new.replace(m, replacement)
                count += 1
            fixes_applied.append(f"regex:{name}")
    
    if new != text:
        path.write_bytes(new.encode("utf-8"))
        fixed += 1
        details.append((str(path.relative_to(ROOT)), count, fixes_applied))
        print(f"FIXED {count:+} chars -> {path.relative_to(ROOT)}")

print(f"\nTotal arquivos corrigidos: {fixed}")
if details:
    print("\nDetalhes:")
    for rel, count, fixes in details:
        print(f"  {rel}: {count} chars, fixes: {fixes}")
