# CTkTextbox

Campo de texto multiline com rolagem vertical e horizontal (quando `wrap='none'`).

## Exemplo sem classes

```python
import customtkinter

textbox = customtkinter.CTkTextbox(app)

textbox.insert("0.0", "new text to insert")           # insere no início
text = textbox.get("0.0", "end")                    # lê tudo
textbox.delete("0.0", "end")                        # limpa tudo
textbox.configure(state="disabled")                  # somente leitura
```

## Exemplo com classes (preenchendo a janela)

```python
import customtkinter

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.textbox = customtkinter.CTkTextbox(master=self, width=400, corner_radius=0)
        self.textbox.grid(row=0, column=0, sticky="nsew")
        self.textbox.insert("0.0", "Some example text!\n" * 50)


app = App()
app.mainloop()
```

> Os índices seguem o padrão do `tkinter.Text` (ex.: `"line.character"`, `"end"`, `"insert"`).

## Argumentos

| Argumento | Descrição |
|---|---|
| `master` | `root`, `Frame` ou `top-level` |
| `width` | Largura em px |
| `height` | Altura em px |
| `corner_radius` | Raio dos cantos em px |
| `border_width` | Largura da borda em px |
| `border_spacing` | Espaço mínimo entre texto e borda (padrão: `3`) |
| `fg_color` | Cor: `(light_color, dark_color)` ou cor única ou `"transparent"` |
| `border_color` | Cor da borda |
| `text_color` | Cor do texto |
| `scrollbar_button_color` | Cor da scrollbar |
| `scrollbar_button_hover_color` | Hover da scrollbar |
| `font` | Fonte: `(font_name, size)` |
| `activate_scrollbars` | `True` (padrão) — exibe scrollbars automaticamente |
| `state` | `"normal"` ou `"disabled"` |
| `wrap` | `"char"` (padrão), `"word"` ou `"none"` |

`CTkTextbox` também aceita argumentos nativos do `tkinter.Text`:

```text
autoseparators, cursor, exportselection, insertborderwidth,
insertofftime, insertontime, insertwidth, maxundo, padx, pady,
selectborderwidth, spacing1, spacing2, spacing3, state, tabs,
takefocus, undo, xscrollcommand, yscrollcommand
```

## Métodos

### `.configure(attribute=value, ...)`

```python
textbox.configure(state=..., text_color=..., ...)
```

### `.cget(attribute_name)`

### `.bind(sequence, command=None, add=None)`

### `.unbind(sequence, funcid=None)`

Desassocia evento usando `funcid` retornado por `.bind()`.

### `.insert(index, text, tags=None)`

### `.delete(index1, index2=None)`

Remove caracteres entre os índices.

### `.get(index1, index2=None)`

Retorna o texto entre os índices.

### `.focus_set()`

Define foco no textbox.

`CTkTextbox` também expõe quase todos os métodos nativos do `tkinter.Text`.
