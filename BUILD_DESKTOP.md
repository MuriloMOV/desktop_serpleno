# Build do SerPleno Desktop

## Configuração

Defina as variáveis descritas em `.env.example` no ambiente da máquina. As
credenciais de banco e URLs não precisam mais ser alteradas no código-fonte.

## Gerar o executável

```powershell
python -m pip install -r requirements-build.txt
python -m PyInstaller --clean --noconfirm SerPleno.spec
```

O executável será criado em `dist/SerPleno.exe`.

## Validação mínima

1. Inicie o backend e o MySQL configurados pelas variáveis de ambiente.
2. Execute `dist/SerPleno.exe`.
3. Valide login, listagem de estudantes e agenda.
4. Repita em uma máquina Windows limpa antes da distribuição.
