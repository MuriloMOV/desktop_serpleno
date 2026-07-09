# CTkImage

Container para até duas imagens PIL — uma para o light mode e outra para o dark mode. Não é um widget; use-o dentro de `CTkLabel` ou onde `image` for aceito.

> Importante: use imagens em resolução maior que o `size` informado, pois o sistema escala por monitor (ex.: em 2x scaling, a imagem deve ter pelo menos `2 * width` e `2 * height`).

## Exemplo

```python
import customtkinter
from PIL import Image

my_image = customtkinter.CTkImage(
    light_image=Image.open("light.png"),
    dark_image=Image.open("dark.png"),
    size=(30, 30)
)

image_label = customtkinter.CTkLabel(app, image=my_image, text="")
image_label.pack(padx=20, pady=20)
```

Se apenas `light_image` ou `dark_image` for passado, a mesma imagem é usada em ambos os modos.

## Argumentos

| Argumento | Descrição |
|---|---|
| `light_image` | `PIL.Image` para light mode |
| `dark_image` | `PIL.Image` para dark mode |
| `size` | Tupla `(width, height)` em px independentemente do scaling |

## Métodos

### `.configure(attribute=value, ...)`

### `.cget(attribute_name)`
