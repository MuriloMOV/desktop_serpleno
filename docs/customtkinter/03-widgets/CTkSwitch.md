# CTkSwitch

Toggle booleano com texto opcional.

## Exemplo

```python
import customtkinter

def switch_event():
    print("switch toggled, current value:", switch_var.get())

switch_var = customtkinter.StringVar(value="on")
switch = customtkinter.CTkSwitch(
    app,
    text="CTkSwitch",
    command=switch_event,
    variable=switch_var,
    onvalue="on",
    offvalue="off"
)
```

## Argumentos

| Argumento | Descrição |
|---|---|
| `master` | `root`, `Frame` ou `Toplevel` |
| `width` | Largura total em px |
| `height` | Altura total em px |
| `switch_width` | Largura do switch em px |
| `switch_height` | Altura do switch em px |
| `corner_radius` | Raio dos cantos em px |
| `border_width` | Largura da borda em px |
| `fg_color` | Cor: `(light_color, dark_color)` ou cor única |
| `border_color` | Cor da borda: `(light_color, dark_color)` ou cor única ou `"transparent"` |
| `progress_color` | Cor quando ligado: `(light_color, dark_color)` ou cor única ou `"transparent"` |
| `button_color` | Cor do botão: `(light_color, dark_color)` ou cor única |
| `button_hover_color` | Hover do botão |
| `hover_color` | Hover do switch |
| `text_color` | Cor do texto |
| `text` | Texto |
| `textvariable` | `tkinter.StringVar` |
| `font` | Fonte: `(font_name, size)` |
| `command` | Função chamada ao alterar |
| `variable` | `tkinter` variable para controle |
| `onvalue` | Valor quando ligado |
| `offvalue` | Valor quando desligado |
| `state` | `"normal"` ou `"disabled"` |

## Métodos

### `.configure(attribute=value, ...)`

```python
switch.configure(state="disabled")
```

### `.cget(attribute_name)`

```python
state = switch.cget("state")
```

### `.get()`

Retorna `1` ou `0`.

### `.select()`

Liga sem chamar `command`.

### `.deselect()`

Desliga sem chamar `command`.

### `.toggle()`

Inverte e chama `command`.
