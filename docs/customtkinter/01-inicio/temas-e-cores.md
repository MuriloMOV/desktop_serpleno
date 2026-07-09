# Temas e Cores

## Cores

Todas as cores dos widgets podem ser customizadas. Os argumentos específicos estão na documentação de cada widget.

**Importante**: `bg_color` é a cor atrás do widget apenas se ele tiver cantos arredondados. A cor principal do widget é chamada de `fg_color`.

![CTkButton color attributes explained](img/color-theme.png)

## Formatos suportados

### Cor única

```python
button = customtkinter.CTkButton(root_tk, fg_color="red")        # nome
button = customtkinter.CTkButton(root_tk, fg_color="#FF0000")     # hexadecimal
```

### Tupla (light, dark)

```python
button = customtkinter.CTkButton(root_tk, fg_color=("#DB3E39", "#821D1A"))
```

A cor é escolhida automaticamente conforme o appearance mode atual.

## Temas padrão

Por padrão, o CustomTkinter usa cores definidas pelo tema. Temas disponíveis: `"blue"` (padrão), `"dark-blue"` e `"green"`.

```python
customtkinter.set_default_color_theme("dark-blue")  # "blue", "green", "dark-blue"
```

## Temas customizados

Um tema é um arquivo `.json`. Você pode criar seu próprio tema copiando um arquivo existente (ex.: `dark-blue.json`), alterar os valores e carregá-lo:

```python
customtkinter.set_default_color_theme("path/to/your/custom_theme.json")
```
