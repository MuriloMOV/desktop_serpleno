# CTkFont

Utilitário para gestão de fontes. Ao contrário da tupla de fontes, `CTkFont` pode ser alterado após criação e compartilhado entre widgets.

## Definição por tupla (não configurável depois)

```python
import customtkinter

button = customtkinter.CTkButton(app, font=("<family>", <size in px>, "<keyword>"))
```

Palavras-chave opcionais: `normal`, `bold`, `roman`, `italic`, `underline`, `overstrike`. Tamanho negativo = pixels.

## Usando `CTkFont` (recomendado)

```python
import customtkinter

font = customtkinter.CTkFont(family="<family>", size=<size in px>, <kwargs>)

button = customtkinter.CTkButton(app, font=font)

# altera depois
font.configure(size=new_size)
```

## Compartilhamento

```python
import customtkinter

font = customtkinter.CTkFont(family="Arial", size=16)

button_1 = customtkinter.CTkButton(app, font=font)
button_2 = customtkinter.CTkButton(app, font=font)

font.configure(family="Helvetica")  # aplica aos dois widgets
```

## Argumentos

| Argumento | Descrição |
|---|---|
| `family` | Nome da família da fonte |
| `size` | Altura em pixels |
| `weight` | `"bold"` ou `"normal"` |
| `slant` | `"italic"` ou `"roman"` |
| `underline` | `True`/`False` |
| `overstrike` | `True`/`False` |

## Métodos

### `.configure(attribute=value, ...)`

Altera qualquer atributo e reflete em todos os widgets usando a fonte.

### `.cget(attribute_name)`

```python
family = font.cget("family")
```

### `.measure(text)`

Retorna a largura em pixels de `text`.

### `.metrics(option=None)`

```python
metrics = font.metrics()      # dicionário completo
ascent = font.metrics("ascent")
```

Métricas disponíveis:
- `ascent`
- `descent`
- `fixed`
- `linespace`
