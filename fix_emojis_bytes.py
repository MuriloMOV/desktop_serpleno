import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

src_root = 'src'

# Mapeamento de bytes corrompidos para corretos
# Estes são os bytes exatos encontrados nos arquivos
replacements_bytes = {
    # 😀"… -> 📅
    b'\xf0\x9f\x98\x80\xe2\x80\x9c\xe2\x80\xa6': '📅',
    # 😀Ž" -> 👥
    b'\xf0\x9f\x98\x80\xc5\xbd\xe2\x80\x9c': '👥',
    # 😀"ˆ -> 📋
    b'\xf0\x9f\x98\x80\xe2\x80\x9c\xcb\x86': '📋',
    # 😀'š -> 💙
    b'\xf0\x9f\x98\x80\xe2\x80\x99\xc5\xa1': '💙',
    # 😀"Ž -> 🔍
    b'\xf0\x9f\x98\x80\xe2\x80\x9c\xc5\xbd': '🔍',
    # 😀'¬ -> 💬
    b'\xf0\x9f\x98\x80\xe2\x80\x99\xc2\xac': '💬',
    # 😀"Œ -> 📢
    b'\xf0\x9f\x98\x80\xe2\x80\x9c\xc5\x92': '📢',
    # 😀" -> 👥
    b'\xf0\x9f\x98\x80\xe2\x80\x9c\xc2\x8d': '👥',
    # 😀' -> 👁
    b'\xf0\x9f\x98\x80\xe2\x80\x99': '👁',
    # 😀" -> 📊
    b'\xf0\x9f\x98\x80\xe2\x80\x9c': '📊',
}

fixed = 0
for root, dirs, files in os.walk(src_root):
    for name in files:
        if not name.endswith('.py'):
            continue
        filepath = os.path.join(root, name)
        with open(filepath, 'rb') as f:
            raw = f.read()

        original = raw
        for old, new in replacements_bytes.items():
            if old in raw:
                raw = raw.replace(old, new.encode('utf-8'))

        if raw != original:
            with open(filepath, 'wb') as f:
                f.write(raw)
            fixed += 1
            print(f'Fixed: {filepath}')

print(f'\nTotal fixes: {fixed}')
