# CTkProgressBar

## Exemplo

```python
progressbar = customtkinter.CTkProgressBar(app, orientation="horizontal")
```

## Argumentos

| Argumento | Descrição |
|---|---|
| `master` | `root`, `tkinter.Frame` ou `CTkFrame` |
| `width` | Largura em px |
| `height` | Altura em px |
| `border_width` | Largura da borda em px |
| `corner_radius` | Raio dos cantos em px |
| `fg_color` | Cor principal: `(light_color, dark_color)` ou cor única |
| `border_color` | Cor da borda |
| `progress_color` | Cor do progresso |
| `orientation` | `"horizontal"` (padrão) ou `"vertical"` |
| `mode` | `"determinate"` ou `"indeterminate"` |
| `determinate_speed` | Velocidade no modo `"determinate"` (padrão: `1`) |
| `indeterminate_speed` | Velocidade no modo `"indeterminate"` (padrão: `1`) |

## Métodos

### `.configure(attribute=value, ...)`

```python
progressbar.configure(mode="indeterminate")
```

### `.cget(attribute_name)`

```python
mode = progressbar.cget("mode")
```

### `.set(value)`

Define o valor do progresso (intervalo de `0` a `1`).

```python
progressbar.set(value)
```

### `.get()`

```python
value = progressbar.get()
```

### `.start()`

Inicia progresso automático.

### `.stop()`

Interrompe o progresso automático.

### `.step()`

Executa um passo manual (similar ao loop de `.start()`).
