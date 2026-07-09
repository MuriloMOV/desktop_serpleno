# CTkButton

## Exemplo

```python


def button_event():
    print("button pressed")

button = customtkinter.CTkButton(app, text="CTkButton", command=button_event)
```

## Argumentos

| Argumento | Descrição |
|---|---|
| `master` | `root`, `tkinter.Frame` ou `CTkFrame` |
| `width` | Largura em px |
| `height` | Altura em px |
| `corner_radius` | Raio dos cantos em px |
| `border_width` | Largura da borda em px |
| `border_spacing` | Espaçamento entre texto/imagem e borda (padrão: `2`) |
| `fg_color` | Cor principal: `(light_color, dark_color)` ou cor única ou `"transparent"` |
| `hover_color` | Cor no hover: `(light_color, dark_color)` ou cor única |
| `border_color` | Cor da borda: `(light_color, dark_color)` ou cor única |
| `text_color` | Cor do texto: `(light_color, dark_color)` ou cor única |
| `text_color_disabled` | Cor do texto desabilitado |
| `text` | Texto do botão |
| `font` | Fonte: `(font_name, size)` — use valor negativo para tamanho em px |
| `textvariable` | `tkinter.StringVar` para alterar o texto |
| `image` | Imagem (`PhotoImage`). Remove o texto |
| `state` | `"normal"` ou `"disabled"` |
| `hover` | `True`/`False` |
| `command` | Função callback |
| `compound` | Orientação de imagem: `"top"`, `"left"`, `"bottom"`, `"right"` |
| `anchor` | Alinhamento: `"n"`, `"ne"`, `"e"`, `"se"`, `"s"`, `"sw"`, `"w"`, `"nw"`, `"center"` |

## Métodos

### `.configure(attribute=value, ...)`

```python
button.configure(text="new text")
```

### `.cget(attribute_name)`

```python
text = button.cget("text")
```

### `.invoke()`

Dispara `command` se o estado não for `disabled`.
