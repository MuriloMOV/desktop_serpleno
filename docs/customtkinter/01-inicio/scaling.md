# Scaling

## Suporte High DPI

CustomTkinter suporta scaling High DPI automaticamente em macOS e Windows:

- **macOS**: Funciona automaticamente para janelas Tk.
- **Windows**: O aplicativo é tornado DPI-aware via `windll.shcore.SetProcessDpiAwareness(2)`. O fator de escala atual é detectado e todos os elementos e geometria são escalados automaticamente.

![Windows 10 scaling settings example](img/windows_scaling.png)

## Desativar scaling automático

```python
customtkinter.deactivate_automatic_dpi_awareness()
```

> A janela ficará borrada no Windows com escala maior que 100%.

## Scaling customizado

Além do fator automático, é possível definir scaling manualmente:

```python
customtkinter.set_widget_scaling(float_value)   # dimensões dos widgets e tamanho de texto
customtkinter.set_window_scaling(float_value)    # geometria da janela
```
