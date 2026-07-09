# CTkToplevel

Usado para criar janelas adicionais. Diferente do `CTk`, o `CTkToplevel` não precisa de chamada a `.mainloop()` — a janela é aberta assim que instanciada.

## Exemplo simples

```python
toplevel = customtkinter.CTkToplevel(app)  # master é opcional
```

## Exemplo integrado

```python
import customtkinter

class ToplevelWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("400x300")

        self.label = customtkinter.CTkLabel(self, text="ToplevelWindow")
        self.label.pack(padx=20, pady=20)


class App(customtkinter.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("500x400")

        self.button_1 = customtkinter.CTkButton(self, text="open toplevel", command=self.open_toplevel)
        self.button_1.pack(side="top", padx=20, pady=20)

        self.toplevel_window = None

    def open_toplevel(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ToplevelWindow(self)
        else:
            self.toplevel_window.focus()


app = App()
app.mainloop()
```

> Checa se a janela já existe antes de criar, evitando múltiplas instâncias.

## Argumentos

| Argumento | Descrição |
|---|---|
| `fg_color` | Cor de fundo: `(light_color, dark_color)` ou cor única |

## Métodos

### `.configure(attribute=value, ...)`

```python
toplevel.configure(fg_color="red")
```

### `.cget(attribute_name)`

```python
fg_color = toplevel.cget("fg_color")
```

### `.title(string)`

Define o título.

### `.geometry(geometry_string)`

Define geometria: `"<width>x<height>"` ou `"<width>x<height>+<x_pos>+<y_pos>"`.

### `.minsize(width, height)`

Tamanho mínimo.

### `.maxsize(width, height)`

Tamanho máximo.

### `.resizable(width, height)`

Define se largura/altura são redimensionáveis (valores booleanos).

### `.after(milliseconds, command)`

Executa `command` após `milliseconds` sem bloquear o loop principal.

### `.withdraw()`

Oculta janela e ícone. Restaure com `.deiconify()`.

### `.iconify()`

Minimiza a janela. Restaure com `.deiconify()`.

### `.deiconify()`

Restaura janela minimizada ou oculta.

### `.state(new_state)`

Define o estado: `'normal'`, `'iconic'`, `'withdrawn'`, `'zoomed'`. Retorna o estado atual se nenhum argumento for passado.
