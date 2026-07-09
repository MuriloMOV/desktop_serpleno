import sys
sys.stdout.reconfigure(encoding='utf-8')

files = [
    'src/ser_pleno/application/controllers/base.py',
    'src/ser_pleno/application/services/agendamentos.py',
    'src/ser_pleno/application/services/estudantes.py',
    'src/ser_pleno/application/services/orientacoes.py',
    'src/ser_pleno/config/operation_mode.py',
    'src/ser_pleno/infrastructure/api/api.py',
    'src/ser_pleno/infrastructure/api/mural.py',
    'src/ser_pleno/infrastructure/api/sync_service.py',
    'src/ser_pleno/presentation/components/ui_components.py',
    'src/ser_pleno/presentation/views/analise_triagem.py',
    'src/ser_pleno/presentation/views/base.py',
    'src/ser_pleno/presentation/views/bem_estar.py',
    'src/ser_pleno/presentation/views/comunicacao_interna.py',
    'src/ser_pleno/presentation/views/estudantes.py',
    'src/ser_pleno/presentation/views/orientacoes.py',
    'src/ser_pleno/presentation/views/quadro_avisos.py',
    'src/ser_pleno/presentation/views/relatorio.py',
    'src/ser_pleno/ui/theme.py',
]

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    corrupted = []
    for i, line in enumerate(lines, 1):
        if '😀' in line or 'ï¸' in line or 'â' in line or 'Ã' in line or '”' in line or '‘' in line:
            corrupted.append((i, line))
    
    if corrupted:
        print(f'\n{filepath}:')
        for i, line in corrupted[:5]:
            print(f'  {i}: {repr(line)}')
