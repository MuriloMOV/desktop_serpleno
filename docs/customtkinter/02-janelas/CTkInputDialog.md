# CTkInputDialog

Dialog simples para entrada de string ou número.

## Exemplo mínimo

```python
import customtkinter

dialog = customtkinter.CTkInputDialog(text="Type in a number:", title="Test")
text = dialog.get_input()  # aguarda entrada
```

## Exemplo em app

```python
import customtkinter

app = customtkinter.CTk()
app.geometry("400x300")


def button_click_event():
    dialog = customtkinter.CTkInputDialog(text="Type in a number:", title="Test")
    print("Number:", dialog.get_input())


button = customtkinter.CTkButton(app, text="Open Dialog", command=button_click_event)
button.pack(padx=20, pady=20)

app.mainloop()
```

## Argumentos

| Argumento | Descrição |
|---|---|
| `title` | Título do dialog |
| `text` | Texto exibido no dialog |
| `fg_color` | Cor da janela: `(light_color, dark_color)` ou cor única |
| `button_fg_color` | Cor dos botões: `(light_color, dark_color)` ou cor única |
| `button_hover_color` | Cor de hover dos botões: `(light_color, dark_color)` ou cor única |
| `button_text_color` | Cor do texto dos botões: `(light_color, dark_color)` ou cor única |
| `entry_fg_color` | Cor do campo de entrada: `(light_color, dark_color)` ou cor única |
| `entry_border_color` | Cor da borda do campo: `(light_color, dark_color)` ou cor única |
| `entry_text_color` | Cor do texto do campo: `(light_color, dark_color)` ou cor única |

## Métodos

### `.get_input()`

Retorna o valor digitado. Aguarda clique em `Ok` ou `Cancel`.
