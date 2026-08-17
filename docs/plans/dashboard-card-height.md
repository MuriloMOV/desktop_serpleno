# Dashboard — altura excessiva nos cards de “Próximos Atendimentos”

## Racional Arquitetural

A seção de **Próximos Atendimentos** (`_atualizar_secao_agenda`) apresentava cards/linhas verticalmente excessivos em relação às outras seções do dashboard (Alertas, Atendimentos Recentes). Após análise comparativa entre `_AppointmentRow` (agenda/recente) e `_AlertaRow` (alertas), identificamos três vetores de expansão vertical desnecessária:

1. **Padding do Card de agenda**: `padding=(12, 8)` gera ~37 px de espaçamento vertical fixo no wrapper, contra ~33 px dos cards de alertas/recentes (`padding=(8, 6)`). Diferença de 4 px por card.
2. **Corner radius grande no frame da linha**: `_AppointmentRow` usa `corner_radius=RADIUS["lg"]` (= 12). Em CustomTkinter 5.2.2, frames com `corner_radius` significativo tendem a reivindicar altura mínima adicional para renderização dos arredondamentos.
3. **Espaçamento interno acumulado na linha**: `pady=2` na label do `time_frame` + `pady=(spacing("xs"), 0)` na label de curso + `pady=1` na grid + `pady=1` no pack externo.

**Causa raiz adicional descoberta**: O `NavigationManager` mantém um **cache de views** (`_view_cache`). Quando o dashboard é reexibido, a mesma instância de `DashboardFrame` é reutilizada, e dentro dela, os cards (`_agenda_card`, `_alert_card`, etc.) também são reutilizados sem recriação. Isso significa que alterações de padding/título feitas no código não surtem efeito se a view já estiver cacheada, pois o widget existente mantém os atributos antigos.

## Decisão

Aplicar ajustes **incrementais e reversíveis** focados em compactar a linha de agenda sem quebrar o design system:

- Reduzir `corner_radius` de `_AppointmentRow` de `RADIUS["lg"]` para `RADIUS["md"]` (12 → 8).
- Reduzir padding do Card de agenda de `(12, 8)` para `(12, 4)`.
- Reduzir `pady` externo entre linhas de `1` para `0`.
- Reduzir `pady` da label de curso de `(spacing("xs"), 0)` para `(2, 0)`.
- Reduzir `pady` da label do `time_frame` de `2` para `1`.

**Correção de cache**: Para garantir que alterações de layout surtam efeito imediatamente, modificar todos os métodos de atualização de seção do dashboard para **destruir o card antigo** (se existir) antes de criar um novo, em vez de reutilizar o widget cacheado. Isso elimina a dependência de recriação do `DashboardFrame` para aplicar mudanças de padding/título.

## Backlog

### [Configuração de Ambiente]
- [x] Nenhuma dependência nova requerida.

### [Execução/Desenvolvimento]
- [x] Ajustar `_AppointmentRow.__init__`: `corner_radius=RADIUS["md"]`.
- [x] Ajustar `_atualizar_secao_agenda`: `padding=(12, 4)` no Card.
- [x] Ajustar pack externo das linhas: `pady=0`.
- [x] Ajustar `pady` da label de curso: `(2, 0)`.
- [x] Ajustar `pady` da label do `time_frame`: `1`.
- [x] Modificar todos os métodos `_atualizar_secao_*` para destruir o card cacheado antes de recriar.

### [Validação/QA]
- [ ] Executar `pytest -v --tb=short` e garantir que nenhum teste quebre.
- [ ] Inspeção visual: abrir dashboard, navegar para outra tela e voltar para verificar altura das linhas de agenda vs alertas/recentes.

## Critérios de Aceite

- Linhas de “Próximos Atendimentos” ficam visualmente alinhadas em altura com as linhas de “Estudantes em Alerta” e “Atendimentos Recentes”.
- Nenhum teste automatizado existente quebra.
- Alterações de padding/título nos cards do dashboard surtem efeito imediatamente após reload de dados, sem necessidade de fechar/reabrir o app.
- Mantido 100% de compatibilidade com `CustomTkinter 5.2.2` (sem `auto_body`, sem `border_color == fg_color` para cantos arredondados).
