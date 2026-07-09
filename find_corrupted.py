import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

src_root = 'src'
patterns = ['Ã', 'Â', 'â', 'ð', 'ï¸', '”€', '😀']

for root, dirs, files in os.walk(src_root):
    for name in files:
        if not name.endswith('.py'):
            continue
        filepath = os.path.join(root, name)
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        found = [p for p in patterns if p in content]
        if found:
            print(f'{filepath}: {found}')
