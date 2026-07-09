# CTkOptionMenu

Dropdown de opções. Utiliza `StringVar` e `command` callback.

## Exemplo — sem variável

```python
import customtkinter

def optionmenu_callback(choice):
    print("optionmenu dropdown clicked:", choice)

optionmenu = customtkinter.CTkOptionMenu(
    app,
    values=["option 1", "option 2"],
    command=optionmenu_callback
)
optionmenu.set("option 2")
```

## Exemplo — com variável

```python
import customtkinter

def optionmenu_callback(choice):
    print("optionmenu dropdown clicked:", choice)

optionmenu_var = customtkinter.StringVar(value="option 2")
optionmenu = customtkinter.CTkOptionMenu(
    app,
    values=["option 1", "option 2"],
    command=optionmenu_callback,
    variable=optionmenu_var
)
```

## Argumentos

| Argumento | Descrição |
|---|---|
| `master` | `root`, `Frame` ou `top-level` |
| `width` | Largura em px |
| `height` | Altura em px |
| `corner_radius` | Raio dos cantos em px |
| `fg_color` | Cor interna: `(light_color, dark_color)` ou cor única |
| `button_color` | Cor do botão direito |
| `button_hover_color` | Hover do botão direito |
| `dropdown_fg_color` | Fundo do dropdown |
| `dropdown_hover_color` | Hover do dropdown |
| `dropdown_text_color` | Texto do dropdown |
| `text_color` | Cor do texto selecionado |
| `text_color_disabled` | Cor do texto desabilitado |
| `font` | Fonte: `(font_name, size)` |
| `dropdown_font` | Fonte do dropdown |
| `hover` | `True`/`False` |
| `state` | `"normal"` ou `"disabled"` |
| `command` | Função chamada ao selecionar |
| `variable` | `StringVar` para controle/leitura |
| `values` | Lista de strings das opções |
| `dynamic_resizing` | Redimensionar automaticamente (`True` padrão) |
| `anchor` | Orientação do texto: `"n"`, `"s"`, `"e"`, `"w"`, `"center"` (padrão: `"w"`) |

## Métodos

### `.configure(attribute=value, ...)`

```python
optionmenu.configure(values=["new value 1", "new value 2"])
```

### `.cget(attribute_name)`

```python
state = optionmenu.cget("state")
```

### `.set(value)`

Define um valor visível (não precisa estar em `values`).

```python
optionmenu.set("option 2")
```

### `.get()`

Retorna o valor atual.
