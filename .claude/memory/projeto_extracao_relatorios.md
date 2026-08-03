---
name: projeto-extracao-relatorios
description: "Estado pós-rename (03/08/2026): o antigo SGR agora se chama Relatórios (repo arecomarcelo/relatorios) e mantém produção em relatorios.oficialsport.com.br; a app Django de extração agora é arecomarcelo/relatorios-novo"
metadata:
  type: project
  originSessionId: sessao-2026-08-03-note-oficial
---

**Atualizado em 03/08/2026** — ver [[projeto_renomeado_relatorios]] para o rename completo (pasta/repo/infra). Contexto original (antes do rename), preservado para histórico:

Confirmado em 03/08/2026 (Note_Oficial, Claude Code) via busca no código + GitHub API + curl no domínio, ANTES do rename:
- O SGR (Streamlit, este repositório, então `arecomarcelo/sgr`) era o app publicado em `https://relatorios.oficialsport.com.br`.
- O repositório `arecomarcelo/relatorios` era uma app Django nova e separada (stack `manage.py`/`apps/`/`config/`/gunicorn, padrão `.os-*` do ambiente Oficial), gerada pela skill `00-gerar-planejamento` em 22/07/2026 (Note_Casa), extraindo parcialmente o SGR: módulos Estoque, Dashboard de Vendas, Pedidos, Recebimentos, Comex e SAC, em Django puro + Tabulator.js/HTMX. Apps internas do repo: `accounts`, `comex`, `core`, `estoque`, `recebimentos`, `sac`, `vendas`.
- Plano de virada original: quando a nova app Django estivesse validada localmente, assumiria o domínio `relatorios.oficialsport.com.br`, substituindo o SGR.

**O que mudou em 03/08/2026 (rename organizacional/temporário, a pedido do usuário — NÃO é reversão definitiva do plano de virada, confirmado explicitamente pelo usuário):**
- O repositório antigo `arecomarcelo/relatorios` (Django) foi renomeado para `arecomarcelo/relatorios-novo`.
- O SGR (Streamlit) foi renomeado para `arecomarcelo/relatorios` — assumindo o nome "Relatórios" em produção (pasta local, repo GitHub, infraestrutura VPS, branding interno).
- O usuário confirmou que isso é apenas uma reorganização de nomes por ora — a decisão de qual codebase acaba vencendo o domínio a longo prazo pode mudar de novo no futuro.

**Como aplicar:** se o usuário perguntar sobre o status da extração ou por que os nomes mudaram, explicar que hoje `arecomarcelo/relatorios` = o app Streamlit legado (antigo SGR, em produção real); `arecomarcelo/relatorios-novo` = a extração Django (ainda em desenvolvimento local na Note_Casa, não publicada). Não presumir que mudanças em um aparecem no outro — continuam sendo codebases 100% independentes. Se/quando a extração Django for finalizada e assumir o domínio, os nomes provavelmente mudarão de novo (ex.: `relatorios-novo` → `relatorios`, e o Streamlit legado sendo aposentado ou renomeado para algo como `relatorios-legado`) — perguntar ao usuário nessa ocasião, não presumir.
