# CTkEntry

## Exemplo

```python
entry = customtkinter.CTkEntry(app, placeholder_text="CTkEntry")
```

> `CTkEntry` aceita todos os argumentos nativos do `tkinter.Entry` listados abaixo, além dos seus próprios.

## Argumentos

| Argumento | Descrição |
|---|---|
| `master` | `root`, `tkinter.Frame` ou `CTkFrame` |
| `textvariable` | `tkinter.StringVar` |
| `width` | Largura em px |
| `height` | Altura em px |
| `corner_radius` | Raio dos cantos em px |
| `fg_color` | Cor do campo: `(light_color, dark_color)` ou cor única |
| `border_color` | Cor da borda |
| `placeholder_text_color` | Cor do placeholder |
| `placeholder_text` | Texto placeholder |
| `font` | Fonte: `(font_name, size)` |
| `state` | `"normal"` ou `"disabled"` |
| `text_color` | Cor do texto |
| `text_color_disabled` | Cor do texto quando desabilitado |

### Argumentos herdados do `tkinter.Entry`

```text
exportselection, insertborderwidth, insertofftime, insertontime,
insertwidth, justify, selectborderwidth, show, takefocus,
validate, validatecommand, xscrollcommand
```

## Métodos

### `.configure(attribute=value, ...)`

```python
entry.configure(state="disabled")
```

### `.cget(attribute_name)`

```python
state = entry.cget("state")
```

### `.bind(sequence, command, add=None)`

Associa um callback a um evento.

### `.delete(first_index, last_index=None)`

Remove caracteres. Se `last_index` for omitido, remove apenas o caractere em `first_index`.

### `.insert(index, string)`

Insere `string` antes do caractere em `index`.

### `.get()`

Retorna o texto atual.

### `.focus()` / `.focus_force()`

Define foco no entry.

### `.index(index)`

### `.icursor(index)`

### `.select_adjust(index)`

### `.select_from(index)`

### `.select_clear()`

### `.select_present()`

### `.select_range(start_index, end_index)`

### `.select_to(index)`

### `.xview()` / `.xview_moveto(f)` / `.xview_scroll(number, what)`
