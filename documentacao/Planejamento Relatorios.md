---
title: Planejamento da Automação Diária de Relatórios (SGR)
description: Escopo e benchmark da geração e entrega diária dos relatórios de vendas do SGR.
version: 1.0.0
status: Oficial
owner: Oficial Sport
authors:
  - Marcelo Areco
created: 2026-09-29
updated: 2026-09-29
---

# Planejamento da Automação Diária de Relatórios

## Contexto e escopo

Este documento formaliza o escopo incremental da automação diária solicitada para o SGR legado (Streamlit): gerar os relatórios de vendas do dia anterior e encaminhar três capturas PNG ao `#oficial-ti`. O SGR legado foi declarado concluído e em produção no Score central em 19/08/2026; este benchmark acompanha somente a nova automação, sem reclassificar o escopo histórico da aplicação. Não confundir este repositório com `relatorios-novo`, a extração Django separada.

Regra funcional: o único filtro aplicado é o período de datas, com `data_inicio = data_fim = dia anterior` no fuso `America/Sao_Paulo`; vendedor, situação e origem permanecem sem seleção.

## Fase 1 — Período e filtros

- [x] Calcular dinamicamente o dia anterior no fuso `America/Sao_Paulo`.
- [x] Usar a mesma data como início e fim do período.
- [x] Manter vendedor, situação e origem sem seleção; validar que a consulta retorna apenas registros do dia solicitado.

## Fase 2 — Relatórios PNG

- [x] Gerar a captura de Métricas de Vendas a partir da interface real do SGR.
- [x] Gerar a captura do Ranking de Vendedores a partir da interface real do SGR.
- [x] Gerar a captura do Ranking de Produtos a partir da interface real do SGR.
- [x] Validar conteúdo, dimensões e ausência de cortes; testar a consistência básica dos totais e executar os testes automatizados do cálculo/período.

## Fase 3 — Agendamento e entrega

- [x] Configurar o job diário no Hermes Cron, perfil `ti`, às 07:30 (`America/Sao_Paulo`), com destino `slack:C0C4T76PJ67` e validação dos três arquivos antes da entrega.
- [ ] Confirmar a primeira execução automática do Cron e o recebimento dos três PNGs no canal Slack.

## Percentual de desenvolvimento

A geração de validação executada em 29/09/2026 produziu os três PNGs para 28/09/2026, com início e fim iguais e somente os filtros de data. A primeira execução agendada, para 30/09/2026 às 07:30, ainda não ocorreu; por isso a confirmação de entrega automática permanece pendente.

GERAL    ██████████████████░░  89%  8 / 9 etapas

**Realizado em VPS via Hermes VPS**
