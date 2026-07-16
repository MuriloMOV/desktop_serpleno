# Build do SerPleno Desktop

## Pré-requisitos na máquina de build

- Windows 10/11 64-bit
- Python >= 3.11, < 3.14 (recomendado: Python 3.11 ou 3.12)
- Git (opcional, para clonar o repositório)

> **Nota:** A build NÃO precisa do MySQL instalado localmente, apenas das credenciais válidas configuradas no `.env`.

---

## 1. Clonar / copiar o projeto

```powershell
git clone <url-do-repositorio>
cd desktop_serpleno
```

Ou copie a pasta do projeto para a máquina de build.

---

## 2. Criar ambiente virtual

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Se houver erro de política de execução no PowerShell, rode antes:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Bypass -Force
```

---

## 3. Instalar dependências

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-build.txt
```

> **Atenção:** O `pyproject.toml` usa `setuptools.build_meta` como backend. Se aparecer erro de backend indisponível, atualize o setuptools com o comando acima.

---

## 4. Configurar variáveis de ambiente

Copie o arquivo de exemplo:

```powershell
Copy-Item .env.example .env
```

Edite `.env` com as credenciais do ambiente de destino:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=usuario
DB_PASSWORD=senha
DB_NAME=ser_pleno
API_URL=https://api.serpleno.com.br
```

O `.env` é empacotado automaticamente dentro do executável.

---

## 5. Gerar o executável

```powershell
python -m PyInstaller --clean --noconfirm SerPleno.spec
```

O resultado será a pasta `dist\SerPleno\` contendo:

- `SerPleno.exe` — executável principal
- `_internal\` — dependências e recursos empacotados

---

## 6. Validar

1. Execute `dist\SerPleno\SerPleno.exe` na mesma máquina de build.
2. Valide login, listagem de estudantes e agenda.
3. Repita o teste em uma máquina Windows limpa antes da distribuição.

---

## Distribuição

Empacote a pasta `dist\SerPleno\` completa (não distribua apenas o `.exe` isolado).

Para compactar:

```powershell
Compress-Archive -Path dist\SerPleno\* -DestinationPath dist\SerPleno.zip
```

---

## Troubleshooting

| Erro | Causa | Solução |
|------|-------|---------|
| `Cannot import 'setuptools.backends.legacy'` | Backend desatualizado no `pyproject.toml` | `python -m pip install --upgrade setuptools` |
| `ModuleNotFoundError: No module named 'ser_pleno'` | Python não encontra o pacote | Instale o projeto com `python -m pip install -e .` antes do PyInstaller |
| Tela branca / crash no startup | `.env` ausente ou variáveis inválidas | Copie `.env.example` para `.env` e preencha as credenciais |
| Falta de ícones / assets | Pasta `assets` não encontrada | Verifique se `src\ser_pleno\assets\` existe no projeto |

---

## Comandos úteis

```powershell
# Limpar build anterior
Remove-Item -Recurse -Force build, dist, *.spec

# Rebuild completo
python -m PyInstaller --clean --noconfirm SerPleno.spec

# Ver tamanho do executável
Get-ChildItem dist\SerPleno\SerPleno.exe | Select-Object Length
```
