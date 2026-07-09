# CTkLabel

Exibe texto e/ou imagem.

## Exemplo

```python
label = customtkinter.CTkLabel(app, text="CTkLabel", fg_color="transparent")
```

## Argumentos

| Argumento | Descrição |
|---|---|
| `master` | `root`, `tkinter.Frame` ou `CTkFrame` |
| `textvariable` | `tkinter.StringVar` |
| `text` | Texto exibido |
| `width` | Largura em px |
| `height` | Altura em px |
| `corner_radius` | Raio dos cantos em px |
| `fg_color` | Fundo: `(light_color, dark_color)`, cor única ou `"transparent"` |
| `text_color` | Cor do texto: `(light_color, dark_color)` ou cor única |
| `font` | Fonte: `(font_name, size)` |
| `anchor` | Alinhamento do texto no espaço disponível: `"n"`, `"ne"`, `"e"`, `"se"`, `"s"`, `"sw"`, `"w"`, `"nw"`, `"center"` (padrão: `"center"`) |
| `compound` | Relação imagem/texto: `"center"`, `"top"`, `"bottom"`, `"left"`, `"right"` |
| `justify` | Alinhamento de múltiplas linhas: `"left"`, `"center"`, `"right"` |
| `padx` | Espaço extra horizontal (padrão: `1`) |
| `pady` | Espaço extra vertical (padrão: `1`) |

`CTkLabel` também aceita os argumentos nativos do `tkinter.Label`.

## Métodos

### `.configure(attribute=value, ...)`

```python
label.configure(text="new text")
```

### `.cget(attribute_name)`

```python
text = label.cget("text")
```

### `.bind(sequence=None, command=None, add=None)`

Associa eventos ao label.
