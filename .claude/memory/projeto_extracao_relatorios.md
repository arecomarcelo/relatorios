---
name: projeto-extracao-relatorios
description: "SGR está sendo extraído para uma nova app Django 'Relatórios' (repo separado) que assumirá o domínio relatorios.oficialsport.com.br na virada"
metadata:
  type: project
  originSessionId: sessao-2026-08-03-note-oficial
---

Confirmado em 03/08/2026 (Note_Oficial, Claude Code) via busca no código do SGR + GitHub API + curl no domínio:

- **O SGR (Streamlit, este repositório, remote `git@github.com:arecomarcelo/sgr.git`) É o app atualmente publicado em `https://relatorios.oficialsport.com.br`** — confirmado por: (1) `curl` no domínio retorna o bundle estático do Streamlit (index.html com comentário de copyright Streamlit Inc., servido via LiteSpeed); (2) `page_title="SGR"` configurado em `app.py:15` bate com o app rodando ali (Docker, mesma VPS oficial); (3) o PRD do repo `relatorios` (ver abaixo) confirma explicitamente: *"o SGR (Streamlit) continua em produção (Docker, mesma VPS, relatorios.oficialsport.com.br) até que a nova app esteja validada localmente"*.
- **O repositório `git@github.com:arecomarcelo/relatorios.git` NÃO é o SGR** — é uma app Django **nova e separada** (stack `manage.py`/`apps/`/`config/`/gunicorn, padrão `.os-*` do ambiente Oficial), gerada pela skill `00-gerar-planejamento` em 22/07/2026 (Note_Casa), que está **extraindo parcialmente** o SGR: módulos Estoque, Dashboard de Vendas, Pedidos, Recebimentos, Comex e SAC, em Django puro + Tabulator.js/HTMX (substituindo Streamlit+AG Grid). Apps internas do repo: `accounts`, `comex`, `core`, `estoque`, `recebimentos`, `sac`, `vendas`.
- **Plano de virada (decisão já confirmada, não é acidente/colisão):** quando a nova app `relatorios` estiver validada localmente, ela assume o mesmo subdomínio `relatorios.oficialsport.com.br`, substituindo o SGR antigo nesse endereço. Até lá, os dois nomes "SGR" convivem com significados diferentes: legado = "Sistema de Gestão de Recursos" (Streamlit), novo = "Sistema de Gerenciamento de Relatórios" (Django).

**Como aplicar:** se o usuário perguntar sobre o status da extração, sobre por que existem dois repositórios com propósito parecido, ou pedir para alterar algo em "relatorios.oficialsport.com.br", checar se a intenção é no SGR (Streamlit, ainda em produção nesse domínio) ou no repo `relatorios` (Django, ainda em desenvolvimento local, ainda não publicado nesse domínio). Não presumir que mudanças no SGR aparecerão automaticamente na futura app Django, e vice-versa — são codebases 100% independentes.
