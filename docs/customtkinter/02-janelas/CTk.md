# CTk

Janela principal do CustomTkinter. O `CTk` é a base de qualquer programa CustomTkinter e há apenas uma instância com uma chamada de `.mainloop()`.

## Exemplos

### Sem classes

```python
import customtkinter

app = customtkinter.CTk()
app.geometry("600x500")
app.title("CTk example")

app.mainloop()
```

### Com classes

```python
import customtkinter

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("600x500")
        self.title("CTk example")

        self.button = customtkinter.CTkButton(self, command=self.button_click)
        self.button.grid(row=0, column=0, padx=20, pady=10)

    def button_click(self):
        print("button click")

app = App()
app.mainloop()
```

## Argumentos

| Argumento | Descrição |
|---|---|
| `fg_color` | Cor de fundo da janela: `(light_color, dark_color)` ou cor única |

## Métodos

### `.configure(attribute=value, ...)`

Todos os atributos podem ser configurados:

```python
app.configure(fg_color=new_fg_color)
```

### `.cget(attribute_name)`

Recupera o valor atual:

```python
fg_color = app.cget("fg_color")
```

### `.title(string)`

Define o título da janela.

### `.geometry(geometry_string)`

Define geometria: `"<width>x<height>"` ou `"<width>x<height>+<x_pos>+<y_pos>"`.

### `.minsize(width, height)`

Tamanho mínimo da janela.

### `.maxsize(width, height)`

Tamanho máximo da janela.

### `.resizable(width, height)`

Define se largura/altura podem ser redimensionadas com valores booleanos.

### `.after(milliseconds, command)`

Executa `command` após `milliseconds` sem bloquear o main loop.

### `.withdraw()`

Oculta a janela e o ícone. Restaure com `.deiconify()`.

### `.iconify()`

Minimiza a janela. Restaure com `.deiconify()`.

### `.deiconify()`

Restaura janela minimizada ou oculta.

### `.state(new_state)`

Define o estado da janela: `'normal'`, `'iconic'`, `'withdrawn'`, `'zoomed'`. Retorna o estado atual se nenhum argumento for passado.
