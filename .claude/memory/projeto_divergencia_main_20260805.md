---
name: projeto-divergencia-main-20260805
description: "Em 05/08/2026 o main do repo relatorios estava divergido (4 commits locais da Note_Casa x 128 do remoto) — histórias não relacionadas (main do GitHub reescrito com a linhagem Streamlit); trabalho Django preservado em backup/note-casa-django-20260723"
metadata:
  type: project
  originSessionId: sessao-2026-08-05-vps-hermes
  modified: 2026-08-05T14:30:00.000Z
---

## Divergência do main resolvida em 05/08/2026 (VPS via Hermes VPS)

Durante o `sincronizar-sessao` de 05/08/2026, o repo `relatorios` apareceu divergido: local `ahead 4, behind 128`. O usuário optou por `git pull --rebase` para preservar os commits locais.

**Achado importante:** os 4 commits locais (Note_Casa, 22-23/07/2026: `56e8d11b` "Inicialização do projeto relatorios", `14d54f72`, `5ce97312`, `8668294c` "sync: alterações automáticas") e a linhagem do remoto (`626608e4`, 128 commits) **não têm ancestral comum** — o `main` do GitHub foi **reescrito** (force-push) com a linhagem do SGR Streamlit renomeado para "Relatórios" (commits "Renomeia projeto de SGR para Relatórios", "Mescla histórico de deploy/dockerização do SGR..."). O `git pull --rebase` descartou silenciosamente os 4 commits locais — o trabalho Django (init do projeto + app estoque com models/views/templates + documentação/memórias, ~380 inserções) **não existe no remoto**.

**O que foi feito:**
- Trabalho preservado na branch local `backup/note-casa-django-20260723` (aponta para `8668294c`) — objeto ainda existe no disco da VPS.
- Decisão do usuário: **manter `main` = `origin/main`** (linhagem Streamlit do SGR renomeado) e deixar o trabalho Django apenas na branch de backup, **sem push** (nada destrutivo).
- `main` local = `origin/main` = `626608e4`, árvore limpa.

**Regra para sessões futuras:**
- NÃO force-push nem tente "recuperar" os commits Django para o `main` — o usuário decidiu manter a linhagem Streamlit como oficial deste repo.
- A extração Django de verdade vive no repo separado `relatorios-novo` (ver [[projeto_extracao_relatorios]]) — o trabalho da branch de backup é um esboço antigo paralelo, preservado só por segurança.
- Se a branch `backup/note-casa-django-20260723` for removida por limpeza, o trabalho pode ser recuperado de `git reflog`/`git fsck` enquanto os objetos existirem.
