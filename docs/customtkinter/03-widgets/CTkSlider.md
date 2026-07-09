# CTkSlider

Controle deslizante com suporte a variáveis e callbacks.

## Exemplo

```python
import customtkinter

def slider_event(value):
    print(value)

slider = customtkinter.CTkSlider(app, from_=0, to=100, command=slider_event)
```

## Argumentos

| Argumento | Descrição |
|---|---|
| `master` | `root`, `tkinter.Frame` ou `CTkFrame` |
| `command` | Callback recebendo o valor atual |
| `variable` | `tkinter.IntVar` ou `tkinter.DoubleVar` |
| `width` | Largura em px |
| `height` | Altura em px |
| `border_width` | Espaço ao redor do trilho em px |
| `from_` | Valor mínimo |
| `to` | Valor máximo |
| `number_of_steps` | Quantidade de passos discretos |
| `fg_color` | Cor: `(light_color, dark_color)` ou cor única |
| `progress_color` | Cor do trilho preenchido |
| `border_color` | Cor da borda |
| `button_color` | Cor do botão deslizante |
| `button_hover_color` | Hover do botão |
| `orientation` | `"horizontal"` (padrão) ou `"vertical"` |
| `state` | `"normal"` ou `"disabled"` |
| `hover` | `True`/`False` |

## Métodos

### `.configure(attribute=value, ...)`

```python
slider.configure(number_of_steps=25)
```

### `.cget(attribute_name)`

```python
value = slider.cget("from_")
```

### `.set(value)`

```python
slider.set(50)
```

### `.get()`

```python
value = slider.get()
```
