# CTkTabview

Tabs semelhantes a `tkinter.Notebook`. Cada aba é um `CTkFrame`.

## Exemplo sem classes

```python
import customtkinter

tabview = customtkinter.CTkTabview(master=app)
tabview.pack(padx=20, pady=20)

tabview.add("tab 1")
tabview.add("tab 2")
tabview.set("tab 2")

button = customtkinter.CTkButton(master=tabview.tab("tab 1"))
button.pack(padx=20, pady=20)
```

## Exemplo com classes

```python
import customtkinter

class MyTabView(customtkinter.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.add("tab 1")
        self.add("tab 2")

        self.label = customtkinter.CTkLabel(master=self.tab("tab 1"))
        self.label.grid(row=0, column=0, padx=20, pady=10)


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.tab_view = MyTabView(master=self)
        self.tab_view.grid(row=0, column=0, padx=20, pady=20)


app = App()
app.mainloop()
```

## Argumentos

| Argumento | Descrição |
|---|---|
| `master` | `root`, `Frame` ou `top-level` |
| `width` | Largura em px (as abas ficam levemente menores) |
| `height` | Altura em px (as abas ficam levemente menores) |
| `corner_radius` | Raio dos cantos em px |
| `border_width` | Largura da borda em px |
| `fg_color` | Cor da área e das abas |
| `border_color` | Cor da borda |
| `segmented_button_fg_color` | Cor de fundo do segmented button |
| `segmented_button_selected_color` | Cor do botão selecionado |
| `segmented_button_selected_hover_color` | Hover do selecionado |
| `segmented_button_unselected_color` | Cor dos botões não selecionados |
| `segmented_button_unselected_hover_color` | Hover dos não selecionados |
| `text_color` | Cor do texto |
| `text_color_disabled` | Cor do texto desabilitado |
| `command` | Função chamada ao trocar de aba |
| `anchor` | Posição do segmented button: `"nw"`, `"n"`, `"ne"`, `"sw"`, `"s"`, `"se"` |
| `state` | `"normal"` ou `"disabled"` |

## Métodos

### `.configure(attribute=value, ...)`

### `.cget(attribute_name)`

```python
value = tabview.cget("fg_color")
```

### `.tab(name)`

Retorna referência para a aba, como um frame.

```python
button = customtkinter.CTkButton(master=tabview.tab("tab 1"))
```

### `.insert(index, name)`

Insere aba em `index`. `name` deve ser único.

### `.add(name)`

Adiciona aba no final. `name` deve ser único.

### `.index(name)`

Retorna índice da aba.

### `.move(new_index, name)`

Move aba para `new_index`.

### `.rename(old_name, new_name)`

Renomeia aba.

### `.delete(name)`

Remove aba.

### `.set(name)`

Torna a aba visível.

### `.get()`

Retorna o nome da aba visível.
