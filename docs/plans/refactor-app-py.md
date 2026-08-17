# Plano: Revisão de boas práticas em `src/ser_pleno/app.py`

## Racional Arquitetural

`app.py` é o ponto de entrada da aplicação desktop. Ele já faz a maior parte do setup corretamente, mas ainda pode ser organizado para reduzir acoplamento, melhorar legibilidade e evitar que a classe `App` acumule responsabilidades que poderiam estar em métodos claramente nomeados. A revisão deve focar em separar setup de janela, inicialização de serviços e fluxo de login sem introduzir DI container ou camadas extras desnecessárias.

## Backlog de Tarefas

### [Configuração de Ambiente]
- [x] Revisar ordem de imports e isolamento do carregamento do `.env`
- [x] Garantir que `app.py` não dependa de módulos com efeitos colaterais pesados antes do setup mínimo

### [Execução/Desenvolvimento]
- [x] Extrair configuração inicial da janela para método dedicado (`_setup_window`)
- [x] Agrupar handlers de exceção globais em helpers nomeados
- [x] Revisar método `iniciar_sistema` para reduzir mistura de fluxo de login + bootstrap + UI
- [x] Converter variáveis temporárias de performance em helper interno quando pertinente
- [x] Adicionar type hints consistentes

### [Validação/QA]
- [x] Validar sintaxe com `py_compile`
- [ ] Validar startup e login manualmente
- [ ] Verificar ausência de regressões em `mainloop`
