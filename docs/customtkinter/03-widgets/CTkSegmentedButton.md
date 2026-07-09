# CTkSegmentedButton

Grupo de botões segmentados. Apenas um botão pode estar selecionado por vez.

## Exemplo — sem variável

```python
import customtkinter

def segmented_button_callback(value):
    print("segmented button clicked:", value)

segmented_button = customtkinter.CTkSegmentedButton(
    app,
    values=["Value 1", "Value 2", "Value 3"],
    command=segmented_button_callback
)
segmented_button.set("Value 1")
```

## Exemplo — com variável

```python
import customtkinter

def segmented_button_callback(value):
    print("segmented button clicked:", value)

segmented_button_var = customtkinter.StringVar(value="Value 1")
segmented_button = customtkinter.CTkSegmentedButton(
    app,
    values=["Value 1", "Value 2", "Value 3"],
    command=segmented_button_callback,
    variable=segmented_button_var
)
```

## Argumentos

| Argumento | Descrição |
|---|---|
| `master` | `root`, `Frame` ou `top-level` |
| `width` | Largura em px |
| `height` | Altura em px |
| `corner_radius` | Raio dos cantos em px |
| `border_width` | Espaço entre botões e bordas do widget |
| `fg_color` | Cor ao redor dos botões |
| `selected_color` | Cor do botão selecionado |
| `selected_hover_color` | Hover do botão selecionado |
| `unselected_color` | Cor dos botões não selecionados |
| `unselected_hover_color` | Hover dos botões não selecionados |
| `text_color` | Cor do texto |
| `text_color_disabled` | Cor do texto desabilitado |
| `font` | Fonte: `(font_name, size)` |
| `values` | Lista de strings — não pode ser vazia |
| `variable` | `StringVar` para controlar o valor |
| `state` | `"normal"` ou `"disabled"` |
| `command` | Função chamada ao clicar |
| `dynamic_resizing` | Redimensionar automaticamente (`True` padrão) |

## Métodos

### `.configure(attribute=value, ...)`

```python
segmented_button.configure(state="disabled")
```

### `.cget(attribute_name)`

```python
state = segmented_button.cget("state")
```

### `.set(value)`

Define o botão selecionado. Se `value` não estiver em `values`, nenhum fica selecionado.

### `.get()`

Retorna o valor selecionado.

### `.insert(index, value)`

Insere novo valor em `index`.

```python
segmented_button.insert(1, "New Value")
```

### `.move(new_index, value)`

Move valor existente para `new_index`.

### `.delete(value)`

Remove valor e atualiza a lista. Se o valor removido estava selecionado, nenhum botão fica ativo.
