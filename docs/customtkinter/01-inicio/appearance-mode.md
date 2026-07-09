# Appearance Mode

O appearance mode define qual cor será usada quando a cor for especificada como tupla `(light_color, dark_color)`. Você pode alterá-lo a qualquer momento:

```python
import customtkinter

customtkinter.set_appearance_mode("system")  # padrão
customtkinter.set_appearance_mode("dark")
customtkinter.set_appearance_mode("light")
```

## Detalhes

- Quando definido como `"system"`, o modo atual é lido do sistema operacional. Se o sistema mudar durante a execução, o visual é adaptado automaticamente.
- No Linux, `"system"` sempre retorna `"light"`, pois a leitura do modo do sistema ainda não é suportada.
