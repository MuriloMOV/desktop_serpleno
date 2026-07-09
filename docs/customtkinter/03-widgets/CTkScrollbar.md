# CTkScrollbar

Barra de rolagem customizada para uso com widgets do CustomTkinter ou `tkinter.Text`.

## Exemplo

```python
import customtkinter

app = customtkinter.CTk()
app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(0, weight=1)

# textbox com scrollbar externa desativada
tk_textbox = customtkinter.CTkTextbox(app, activate_scrollbars=False)
tk_textbox.grid(row=0, column=0, sticky="nsew")

# scrollbar customizada
ctk_textbox_scrollbar = customtkinter.CTkScrollbar(app, command=tk_textbox.yview)
ctk_textbox_scrollbar.grid(row=0, column=1, sticky="ns")

# liga rolagem do textbox à scrollbar customizada
tk_textbox.configure(yscrollcommand=ctk_textbox_scrollbar.set)

app.mainloop()
```

## Argumentos

| Argumento | Descrição |
|---|---|
| `master` | `root`, `tkinter.Frame` ou `CTkFrame` |
| `command` | Função do widget rolável chamada ao mover a barra |
| `width` | Largura em px |
| `height` | Altura em px |
| `corner_radius` | Raio dos cantos em px |
| `border_spacing` | Espaço em px da scrollbar |
| `fg_color` | Cor: `(light_color, dark_color)` ou cor única ou `"transparent"` |
| `button_color` | Cor do botão da barra |
| `button_hover_color` | Hover do botão da barra |
| `minimum_pixel_length` | Comprimento mínimo em px |
| `orientation` | `"vertical"` (padrão) ou `"horizontal"` |
| `hover` | `True`/`False` |

## Métodos

### `.configure(attribute=value, ...)`

### `.cget(attribute_name)`

### `.get()`

```python
start, end = scrollbar.get()
```

### `.set(start_value, end_value)`

Define posição inicial e final.

```python
scrollbar.set(0.0, 1.0)
```
