# Build do Executável SerPleno

Guia oficial para gerar o executável Windows do SerPleno Desktop, cobrindo os dois modos suportados pelo PyInstaller, troubleshooting simples e avançado, além de alternativas.

---

## 1. Pré-requisitos

- Windows 10/11 64-bit
- Python >= 3.11, < 3.14 (recomendado: 3.11 ou 3.12)
- MySQL acessível na máquina de destino ou remota
- Git (opcional, para clonar o repositório)

> **Nota:** A build não precisa do MySQL instalado localmente, mas precisa que o banco de destino esteja acessível e que o `.env` contenha credenciais válidas.

---

## 2. Estrutura relevante do projeto

```
desktop_serpleno/
├── src/
│   └── ser_pleno/
│       ├── app.py                     # Entry point
│       ├── config/
│       │   ├── db_config.py           # Pool MySQL + leitura de SERPLENO_DB_*
│       │   └── operation_mode.py      # Persiste configurações em disco
│       └── assets/                    # Imagens, ícones, temas
├── config/                            # Configurações adicionais
├── .env.example
├── requirements-build.txt
├── SerPleno.spec                      # Definição do build PyInstaller
└── pyproject.toml
```

---

## 3. Configuração obrigatória antes do build

### 3.1 Copiar `.env`

```powershell
Copy-Item .env.example .env
```

### 3.2 Editar `.env`

O executável usa exclusivamente as variáveis definidas no `.env` para conexão com banco e API. Exemplo mínimo:

```env
SERPLENO_API_URL=http://127.0.0.1:8000
SERPLENO_DB_HOST=127.0.0.1
SERPLENO_DB_PORT=3306
SERPLENO_DB_USER=serpleno
SERPLENO_DB_PASSWORD=sua_senha_aqui
SERPLENO_DB_NAME=ser_pleno
```

### 3.3 Criar e ativar venv

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Se houver erro de política de execução no PowerShell:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Bypass -Force
```

### 3.4 Instalar dependências

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-build.txt
python -m pip install -e .
```

`requirements-build.txt` contém apenas:
```
pyinstaller>=6.0,<7.0
```

---

## 4. Os dois modos de build

### 4.1 Modo 1 — Único executável (`onefile`)

Gera apenas `dist\SerPleno.exe`. Todo o conteúdo fica embutido no executável e é extraído para uma pasta temporária em runtime.

**Quando usar:**
- Distribuição simples por e-mail, chat, download direto.
- Não quer lidar com múltiplos arquivos.

**Desvantagens:**
- Startup mais lento por causa da extração.
- Alguns antivírus são mais sensíveis a executáveis autoextraíveis.
- Arquivos de dados empacotados ficam em `_MEIxxxx` temporário e não podem ser modificados externamente com facilidade.

**Configuração do `.spec`:**

```python
# SerPleno.spec (trecho relevante)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    exclude_binaries=False,
    name="SerPleno",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)
```

**Comando de build:**

```powershell
python -m PyInstaller --clean --noconfirm SerPleno.spec
```

**Resultado:**

```
dist/
└── SerPleno.exe
```

---

### 4.2 Modo 2 — Pasta distribuível (`onedir` / `COLLECT`)

Gera `dist\SerPleno\` com o executável e uma pasta `_internal\` contendo todas as dependências e assets.

**Quando usar:**
- Distribuição interna controlada.
- Quer evitar falsos positivos de antivírus.
- Quer poder inspecionar ou substituir arquivos de dados facilmente.
- Quer startup mais rápido.

**Desvantagens:**
- É necessário distribuir a pasta completa, não apenas o `.exe`.

**Configuração do `.spec`:**

```python
# SerPleno.spec (trecho relevante)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SerPleno",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SerPleno",
)
```

**Comando de build:**

```powershell
python -m PyInstaller --clean --noconfirm SerPleno.spec
```

**Resultado:**

```
dist/
└── SerPleno/
    ├── SerPleno.exe
    └── _internal/
        ├── .env
        ├── config/
        ├── ser_pleno/
        │   ├── assets/
        │   └── sql/
        └── ...
```

---

## 5. Como alternar entre os modos

Edite `SerPleno.spec` e ajuste o bloco `EXE`/`COLLECT` conforme a seção 4. Não é necessário alterar o comando de build.

---

## 6. Soluções para erros comuns

### 6.1 Erro: `Cannot import 'setuptools.backends.legacy'`

**Causa:** `setuptools` desatualizado.

**Solução:**
```powershell
python -m pip install --upgrade setuptools
```

---

### 6.2 Erro: `ModuleNotFoundError: No module named 'ser_pleno'`

**Causa:** O PyInstaller não encontra o pacote `ser_pleno` porque ele não está instalado no ambiente.

**Solução:**
```powershell
python -m pip install -e .
```

---

### 6.3 Erro: `No such file or directory: '...operation_config.json'`

**Causa:** O app tenta salvar configurações em um arquivo dentro da pasta temporária do `onefile`, que é somente leitura ou limpa após o fechamento.

**Solução em andamento:** A aplicação já inclui lógica de fallback. Se o erro persistir, prefira o modo `onedir` para builds de produção, pois `_internal\` é gravável durante a execução.

---

### 6.4 Erro: `Access denied for user 'root'@'localhost' (using password: NO)` ou `... (using password: YES)`

**Causa:** Credenciais do MySQL incorretas ou usuário sem permissão.

**Solução:**

1. Verifique se o `.env` está correto e foi copiado antes do build:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Teste a conexão manualmente:
   ```powershell
   mysql -h 127.0.0.1 -P 3306 -u serpleno -p
   ```

3. Ajuste o usuário no MySQL:
   ```sql
   CREATE USER IF NOT EXISTS 'serpleno'@'localhost' IDENTIFIED BY 'sua_senha';
   GRANT ALL PRIVILEGES ON ser_pleno.* TO 'serpleno'@'localhost';
   FLUSH PRIVILEGES;
   ```

4. Atualize a senha no `.env` e rebuild.

---

### 6.5 Erro: `.env` não é carregado dentro do executável

**Causa:** O caminho do `.env` estava sendo calculado incorretamente em runtime no `onefile`.

**Status:** Corrigido no código atual (`app.py` usa `sys._MEIPASS` quando disponível). Se precisar validar, habilite `console=True` temporariamente no `.spec` e verifique os prints de debug.

---

### 6.6 Erro: `Hidden import 'matplotlib' not found` / `'matplotlib.backends.backend_tkagg' not found`

**Causa:** Bibliotecas opcionais não utilizadas diretamente pelo código principal.

**Solução:** Remova `matplotlib` e `matplotlib.backends.backend_tkagg` dos `hiddenimports` no `.spec`, ou instale o pacote se a aplicação realmente o usar.

---

### 6.7 Erro: Tela branca / crash no startup

**Causa:** `.env` ausente, variáveis inválidas ou dependência faltando no build.

**Solução:**
- Garanta que `.env` existe antes de rodar o PyInstaller.
- Verifique se `src\ser_pleno\assets\` existe.
- Rebuild completo:
  ```powershell
  Remove-Item -Recurse -Force build, dist
  python -m PyInstaller --clean --noconfirm SerPleno.spec
  ```

---

## 7. Troubleshooting avançado

### 7.1 Inspecionar o conteúdo do executável

```powershell
pyi-archive_viewer dist\SerPleno.exe
```

Dentro do viewer, pressione `o` para extrair o conteúdo para uma pasta temporária e verifique manualmente se `.env`, `config/` e `assets/` estão presentes.

### 7.2 Verificar logs da aplicação

Em runtime, o SerPleno gera logs em:
```
%APPDATA%\SerPleno\logs\ser_pleno_desktop.log
```

Se não existir, verifique se a pasta `logs/` foi criada na mesma pasta do executável ou na pasta temporária no caso de `onefile`.

### 7.3 Testar conexão MySQL independentemente

Rode este script com as mesmas variáveis do `.env`:

```python
import os
import mysql.connector

conn = mysql.connector.connect(
    host=os.getenv("SERPLENO_DB_HOST", "127.0.0.1"),
    user=os.getenv("SERPLENO_DB_USER", "root"),
    password=os.getenv("SERPLENO_DB_PASSWORD", ""),
    database=os.getenv("SERPLENO_DB_NAME", "ser_pleno"),
    port=int(os.getenv("SERPLENO_DB_PORT", "3306")),
)
print("Conexão OK")
conn.close()
```

### 7.4 Limpar build e rebuildar

```powershell
Remove-Item -Recurse -Force build, dist
python -m PyInstaller --clean --noconfirm SerPleno.spec
```

> **Importante:** não use `Remove-Item *.spec`. Isso apagaria o `SerPleno.spec` acidentalmente.

---

## 8. Distribuição

### 8.1 Modo `onefile`

Empacote apenas `dist\SerPleno.exe`.

Para compactar:
```powershell
Compress-Archive -Path dist\SerPleno.exe -DestinationPath dist\SerPleno.zip
```

### 8.2 Modo `onedir`

Empacote a pasta `dist\SerPleno\` completa. Não distribua apenas o `.exe` isolado.

```powershell
Compress-Archive -Path dist\SerPleno\* -DestinationPath dist\SerPleno.zip
```

---

## 9. Alternativas ao PyInstaller

### 9.1 Nuitka

Compila o código Python para C e gera um binário nativo. Resultado geralmente menor e mais rápido, mas setup mais complexo.

```powershell
python -m pip install --upgrade nuitka
python -m nuitka --standalone --onefile --windows-icon=assets/icon.ico src/ser_pleno/app.py
```

Prós: desempenho melhorado, menor chance de falsos positivos de antivírus.  
Contras: tempo de build maior, compatibilidade mais sensível a versões de Python.

### 9.2 cx_Freeze

Outra alternativa tradicional para gerar executáveis e instaladores no Windows.

```powershell
python -m pip install --upgrade cx_Freeze
```

Prós: instalador nativo MSI/EXE.  
Contras: configuração mais verbosa, menos integração com `datas` do que PyInstaller.

### 9.3 Empacotamento manual com Python embutido

Distribua o projeto junto com um Python embutido (`python.exe`) e scripts de inicialização. Mais usado em cenários internos onde o Python pode ser instalado na máquina alvo.

---

## 10. Recomendação final

Para o SerPleno Desktop, use:

- **Modo `onedir`** para distribuição interna e homologação.
- **Modo `onefile`** apenas se precisar enviar um único arquivo e aceitar startup mais lento.

Em ambos os casos:
- Sempre rebuild após alterar `.env`.
- Teste o `.exe` na mesma máquina de build antes de distribuir.
- Repita o teste em uma máquina Windows limpa se for distribuir externamente.
