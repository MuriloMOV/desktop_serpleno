# CTkRadioButton

Botão de opção exclusivo, geralmente usado com `tkinter.IntVar` ou `tkinter.StringVar`.

## Exemplo

```python
import customtkinter
import tkinter

def radiobutton_event():
    print("radiobutton toggled, current value:", radio_var.get())

radio_var = tkinter.IntVar(value=0)
radiobutton_1 = customtkinter.CTkRadioButton(
    app,
    text="CTkRadioButton 1",
    command=radiobutton_event,
    variable=radio_var,
    value=1
)
radiobutton_2 = customtkinter.CTkRadioButton(
    app,
    text="CTkRadioButton 2",
    command=radiobutton_event,
    variable=radio_var,
    value=2
)
```

## Argumentos

| Argumento | Descrição |
|---|---|
| `master` | `root`, `tkinter.Frame` ou `CTkFrame` |
| `width` | Largura total em px |
| `height` | Altura total em px |
| `radiobutton_width` | Largura do rádio em px |
| `radiobutton_height` | Altura do rádio em px |
| `corner_radius` | Raio dos cantos em px |
| `border_width_unchecked` | Largura da borda quando não selecionado |
| `border_width_checked` | Largura da borda quando selecionado |
| `fg_color` | Cor principal: `(light_color, dark_color)` ou cor única |
| `border_color` | Cor da borda: `(light_color, dark_color)` ou cor única |
| `hover_color` | Cor no hover |
| `text_color` | Cor do texto |
| `text_color_disabled` | Cor do texto desabilitado |
| `text` | Texto |
| `textvariable` | `tkinter.StringVar` para controle do texto |
| `font` | Fonte: `(font_name, size)` |
| `hover` | `True`/`False` |
| `state` | `"normal"` ou desabilitado |
| `command` | Função chamada ao alterar seleção |
| `variable` | `tkinter` variable para ler/controlar estado |
| `value` | Valor atribuído quando selecionado |

## Métodos

### `.configure(attribute=value, ...)`

```python
radiobutton.configure(state="disabled")
```

### `.cget(attribute_name)`

```python
state = radiobutton.cget("state")
```

### `.select()`

Seleciona o botão (define o valor, sem chamar `command`).

### `.deselect()`

Desseleciona o botão (sem chamar `command`).

### `.invoke()`

Simula clique do usuário (chama `command`).
