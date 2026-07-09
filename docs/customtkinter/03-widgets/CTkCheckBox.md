# CTkCheckBox

## Exemplo

```python
import customtkinter

def checkbox_event():
    print("checkbox toggled, current value:", check_var.get())

check_var = customtkinter.StringVar(value="on")
checkbox = customtkinter.CTkCheckBox(
    app,
    text="CTkCheckBox",
    command=checkbox_event,
    variable=check_var,
    onvalue="on",
    offvalue="off"
)
```

## Argumentos

| Argumento | Descrição |
|---|---|
| `master` | `root`, `tkinter.Frame` ou `CTkFrame` |
| `width` | Largura total em px |
| `height` | Altura total em px |
| `checkbox_width` | Largura do checkbox em px |
| `checkbox_height` | Altura do checkbox em px |
| `corner_radius` | Raio dos cantos em px |
| `border_width` | Largura da borda em px |
| `fg_color` | Cor interna: `(light_color, dark_color)` ou cor única |
| `border_color` | Cor da borda: `(light_color, dark_color)` ou cor única |
| `hover_color` | Cor no hover: `(light_color, dark_color)` ou cor única |
| `text_color` | Cor do texto: `(light_color, dark_color)` ou cor única |
| `text_color_disabled` | Cor do texto desabilitado |
| `text` | Texto |
| `textvariable` | `tkinter.StringVar` para controlar o texto |
| `font` | Fonte: `(font_name, size)` |
| `hover` | `True`/`False` |
| `state` | `"normal"` ou desabilitado |
| `command` | Função chamada ao clicar |
| `variable` | `tkinter` variable para ler/controlar estado |
| `onvalue` | Valor quando marcado |
| `offvalue` | Valor quando desmarcado |

## Métodos

### `.configure(attribute=value, ...)`

```python
checkbox.configure(state="disabled")
```

### `.cget(attribute_name)`

```python
text = checkbox.cget("text")
```

### `.get()`

Retorna `1` ou `0`.

### `.select()`

Marca o checkbox (dispara `.set(1)` sem chamar `command`).

### `.deselect()`

Desmarca (dispara `.set(0)` sem chamar `command`).

### `.toggle()`

Inverte o valor e chama `command`.
