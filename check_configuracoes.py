import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('src/ser_pleno/presentation/views/configuracoes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if '😀' in line or 'ï¸' in line or 'â' in line or 'Ã' in line or '”' in line or '‘' in line:
        print(f'{i}: {repr(line)}')
