# CTkScrollableFrame

Frame com barra de rolagem integrada.

## Exemplo básico

```python
import customtkinter

scrollable_frame = customtkinter.CTkScrollableFrame(app, width=200, height=200)
```

## Exemplo com classe

```python
import customtkinter

class MyFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.label = customtkinter.CTkLabel(self)
        self.label.grid(row=0, column=0, padx=20)


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.my_frame = MyFrame(master=self, width=300, height=200)
        self.my_frame.grid(row=0, column=0, padx=20, pady=20)


app = App()
app.mainloop()
```

## Exemplo — preenchendo a janela

```python
import customtkinter

class MyFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.label = customtkinter.CTkLabel(self)
        self.label.grid(row=0, column=0, padx=20)


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.my_frame = MyFrame(master=self, width=300, height=200, corner_radius=0, fg_color="transparent")
        self.my_frame.grid(row=0, column=0, sticky="nsew")


app = App()
app.mainloop()
```

## Argumentos

| Argumento | Descrição |
|---|---|
| `master` | `root`, `Frame` ou `Toplevel` |
| `width` | Largura interna em px |
| `height` | Altura interna em px |
| `corner_radius` | Raio dos cantos em px |
| `border_width` | Largura da borda em px |
| `fg_color` | Cor: `(light_color, dark_color)` ou cor única ou `"transparent"` |
| `border_color` | Cor da borda |
| `scrollbar_fg_color` | Cor da barra de rolagem |
| `scrollbar_button_color` | Cor do botão da barra de rolagem |
| `scrollbar_button_hover_color` | Hover do botão da barra de rolagem |
| `label_fg_color` | Cor do fundo do título |
| `label_text_color` | Cor do texto do título |
| `label_text` | Texto de título do frame |
| `label_font` | Fonte do título |
| `label_anchor` | Alinhamento do título: `"n"`, `"ne"`, `"e"`, `"se"`, `"s"`, `"sw"`, `"w"`, `"nw"`, `"center"` |
| `orientation` | `"vertical"` (padrão) ou `"horizontal"` |

## Métodos

### `.configure(attribute=value, ...)`

### `.cget(attribute_name)`
