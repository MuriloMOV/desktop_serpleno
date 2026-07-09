# CTkComboBox

## Exemplo — sem variável

```python
import customtkinter

def combobox_callback(choice):
    print("combobox dropdown clicked:", choice)

combobox = customtkinter.CTkComboBox(app, values=["option 1", "option 2"], command=combobox_callback)
combobox.set("option 2")
```

## Exemplo — com variável

```python
import customtkinter

def combobox_callback(choice):
    print("combobox dropdown clicked:", choice)

combobox_var = customtkinter.StringVar(value="option 2")
combobox = customtkinter.CTkComboBox(
    app,
    values=["option 1", "option 2"],
    command=combobox_callback,
    variable=combobox_var
)
combobox_var.set("option 2")
```

## Argumentos

| Argumento | Descrição |
|---|---|
| `master` | `root`, `Frame` ou `top-level` |
| `width` | Largura em px |
| `height` | Altura em px |
| `corner_radius` | Raio dos cantos em px |
| `border_width` | Largura da borda em px |
| `fg_color` | Cor interna: `(light_color, dark_color)` ou cor única |
| `border_color` | Cor da borda: `(light_color, dark_color)` ou cor única |
| `button_color` | Cor do botão direito: `(light_color, dark_color)` ou cor única |
| `button_hover_color` | Hover do botão direito |
| `dropdown_fg_color` | Cor de fundo do dropdown |
| `dropdown_hover_color` | Hover do dropdown |
| `dropdown_text_color` | Cor do texto do dropdown |
| `text_color` | Cor do texto: `(light_color, dark_color)` ou cor única |
| `text_color_disabled` | Cor do texto desabilitado |
| `font` | Fonte: `(font_name, size)` |
| `dropdown_font` | Fonte do dropdown: `(font_name, size)` |
| `values` | Lista de valores do dropdown |
| `hover` | `True`/`False` |
| `state` | `"normal"`, `"disabled"` ou `"readonly"` |
| `command` | Função chamada quando o dropdown é aberto |
| `variable` | `StringVar` para controlar/ler o valor atual |
| `justify` | `"left"`, `"right"` ou `"center"` |

## Métodos

### `.configure(attribute=value, ...)`

```python
combobox.configure(values=["new value 1", "new value 2"])
```

### `.cget(attribute_name)`

```python
state = combobox.cget("state")
```

### `.set(value)`

Define um valor string. Não precisa estar em `values`.

```python
combobox.set("option 2")
```

### `.get()`

Retorna o valor atual do campo.
