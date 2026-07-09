# Empacotamento (Packaging)

## Windows — PyInstaller / Auto Py to Exe

Ao gerar um `.exe` com PyInstaller, existem dois pontos obrigatórios:

### 1) Não use `--onefile`

O CustomTkinter inclui arquivos `.json` e `.otf` além de `.py`. O PyInstaller não consegue empacotar esses recursos em um único `.exe`.

Use `--onedir`:

```python
# Não faça isso:
# pyinstaller --onefile main.py
```

### 2) Inclua a pasta `customtkinter`

```bash
pyinstaller --add-data "<caminho/para/site-packages/customtkinter;customtkinter/" main.py
```

Localização no Windows:

```bash
pip show customtkinter
# Local será algo como:
# c:\users\<user_name>\appdata\local\programs\python\python310\lib\site-packages
```

### Exemplo completo (onedir + janela)

```bash
pyinstaller --noconfirm --onedir --windowed --add-data "<CustomTkinter Location>/customtkinter;customtkinter/" "<Path to Python Script>"
```

### Auto Py to Exe

No campo `--additional file` adicione:

```text
<caminho/para/site-packages>/customtkinter;customtkinter/
```

## Observação

O caminho no Windows pode usar `/` ou `\\`. Prefira `/` para evitar problemas com escaping no PowerShell/cmd.
