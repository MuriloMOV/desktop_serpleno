# CTkFrame

Container base do CustomTkinter. Útil para agrupar widgets.

## Exemplo simples

```python
frame = customtkinter.CTkFrame(master=root_tk, width=200, height=200)
```

## Exemplo com classe

```python
import customtkinter

class MyFrame(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.label = customtkinter.CTkLabel(self)
        self.label.grid(row=0, column=0, padx=20)


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("400x200")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.my_frame = MyFrame(master=self)
        self.my_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")


app = App()
app.mainloop()
```

## Argumentos

| Argumento | Descrição |
|---|---|
| `master` | `root`, `Frame` ou `Toplevel` |
| `width` | Largura em px |
| `height` | Altura em px |
| `border_width` | Largura da borda em px |
| `fg_color` | Cor: `(light_color, dark_color)`, cor única ou `"transparent"` |
| `border_color` | Cor da borda |

## Métodos

### `.configure(attribute=value, ...)`

```python
frame.configure(fg_color="red")
```

### `.cget(attribute_name)`

```python
fg_color = frame.cget("fg_color")
```

### `.bind(sequence=None, command=None, add=None)`

Associa eventos ao frame.
