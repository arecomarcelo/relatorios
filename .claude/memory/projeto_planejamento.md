---
name: projeto-planejamento
description: "Planejamento formal (PRD/Blueprint/Backlog/Sprints) já concluído em 22/07/2026, com decisões técnicas fechadas (Tabulator.js, HTMX, padrão .os-*, subdomínio) — próximo passo é 01-iniciar-projeto"
metadata:
  type: project
---

Planejamento formal (skill `00-gerar-planejamento`) concluído em 22/07/2026, em
`/home/areco/Projetos/Oficial/relatorios/planejamento/`:
- `01 - prd.md`
- `02 - blue-print.md` (inclui Matriz de Paridade completa contra o SGR — nenhuma linha
  `Pendente` sem justificativa)
- `03 - backlog.md` (7 épicos, 23 User Stories MVP + 12 itens PÓS-MVP)
- `04 - sprints.md` (SP00 a SP05 — ordem: Estoque → Recebimentos/Comex → Pedidos → SAC →
  Dashboard de Vendas, do mais simples pro mais arriscado)

Contagem de US idêntica entre Backlog e Sprints (23 = 23) — checklist de consistência da skill
já validado.

**Decisões técnicas fechadas neste planejamento:**
- **Grid client-side**: Tabulator.js (não DataTables) — sem dependência de jQuery, consistente
  com o ecossistema `.os-*` (nenhuma app Oficial usa jQuery hoje). Recupera o filtro/ordenação/
  resize instantâneo por coluna que o AG Grid do Streamlit legado tinha.
- **Cascata reativa (só SAC, OS → Produtos)**: HTMX — único ponto do escopo desta leva com
  dependência reativa real entre duas grids (filtrar/selecionar na grid de OS atualiza a grid de
  Produtos sem reload de página). HTMX e Tabulator são novidade no ecossistema — primeira app a
  usar ambos, sem precedente interno.
- **Padrão visual**: `.os-*` (dark-only, `--os-primary:#B4181E`, `--os-secondary:#0592B0`, Work
  Sans, sem Bootstrap como framework — só `bootstrap-icons` via CDN). **Não** é Bootstrap 5.3 +
  Dracula at Night (esse padrão foi superado em 20/07/2026 no ecossistema Oficial). Referência
  viva: `static/css/os.css` e `templates/base_oficial.html` em
  `/home/areco/Projetos/Oficial/multi-financeiro/`. Esta app nasce direto no `.os-*` — a skill
  `09-aplicar-padrao-visual-oficial` é aplicada já no scaffolding inicial, não como migração
  posterior.
- **Subdomínio**: a app vai assumir `relatorios.oficialsport.com.br` na virada, **substituindo**
  o SGR (Streamlit) dockerizado que usa esse mesmo subdomínio hoje — decisão confirmada, não é
  colisão a evitar. Validar o novo vhost antes de desativar o antigo, quando chegar em
  `02-provisionar-vhost-litespeed` (fase futura).
- **Peça visual sem equivalente pronto no `.os-*`**: gauge de meta (Plotly + Kaleido, técnica
  server-side reaproveitada do legado) + ranking 6x2 de vendedores com foto — nenhuma app `.os-*`
  tem gráfico/gauge hoje, é design e implementação novos, por isso fica por último no roadmap
  (SP05).
- **Fotos de vendedores**: migradas de base64 embutido (técnica do legado) para arquivo estático
  servido via `{% static %}` — melhoria real (cacheable), não regressão.

Ver também [[projeto-natureza]] e [[projeto-banco-permissoes]].
