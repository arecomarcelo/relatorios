---
name: projeto-movido-nova-estrutura
description: "SGR foi movido de Projetos/sgr para Projetos/nova-estrutura/sgr em 03/08/2026 — venv recriada, venv desrastreada do git"
metadata:
  type: project
  originSessionId: sessao-2026-08-03-note-oficial
---

Em 03/08/2026 (Note_Oficial, via Claude Code), a pedido do usuário, o projeto foi movido de `/media/areco/Backup/Oficial/Projetos/sgr` para `/media/areco/Backup/Oficial/Projetos/nova-estrutura/sgr` (mesma partição, `mv` simples — `nova-estrutura` já existia como pasta guarda-chuva das apps extraídas do ambiente Oficial: administracao, comex, estoque, multi-financeiro, rh etc.).

**O que foi ajustado:**
- `venv/` recriada do zero no novo caminho (continha paths absolutos hardcoded em `pyvenv.cfg`, `activate*` e shebangs de `venv/bin/*` — não é portável entre caminhos).
- Descoberto e corrigido efeito colateral pré-existente: 24 arquivos de `venv/bin/` estavam rastreados pelo git apesar de `venv/` já estar no `.gitignore`. Rodado `git rm -r --cached venv` (fica staged, não commitado — decisão de commitar ou não fica com o usuário/hook de auto-commit).
- Nenhuma outra dependência de caminho absoluto encontrada: `.env`, `.streamlit/secrets.toml`, `app/settings.py` (`BASE_DIR` via `Path(__file__)`) e `core/logging_config.py` (`Path("logs")` relativo) já eram portáveis.
- Validado com `python manage.py check` (Django OK) e imports de `streamlit`/`django` na venv nova.
- Deploy de produção (VPS, Docker) **não é afetado** — é um clone/deploy separado na VPS, independente deste caminho local de desenvolvimento.

**Pendências conhecidas (não resolvidas nesta sessão, fora do escopo do pedido):**
- Existe uma pasta `sgr (cópia)` em `/media/areco/Backup/Oficial/Projetos/` (mesma data de modificação da pasta original) — não foi tocada, não se sabe sua origem/propósito; não presumir que é lixo a remover sem perguntar ao usuário.
- A origem exata do hook de auto-commit (ver [[projeto_autocommit]]) não foi localizada (não está em crontab, systemd nem aliases do shell desta máquina) — se ele referenciar o caminho absoluto antigo em algum lugar não investigado (ex.: outra máquina, serviço externo), pode ter parado de funcionar após o move.
- As mudanças staged (`git rm --cached venv`) e a entrada em `Historico.md` não foram commitadas por esta sessão — só commitar mediante pedido explícito do usuário.

**Como aplicar:** o caminho canônico do projeto agora é `/media/areco/Backup/Oficial/Projetos/nova-estrutura/sgr` — usar esse caminho em qualquer referência futura. Esta memória (e as demais do projeto) foi migrada para o novo diretório de memória canônico do Claude Code (`~/.claude/projects/-media-areco-Backup-Oficial-Projetos-nova-estrutura-sgr/memory/`); o diretório antigo (`-media-areco-Backup-Oficial-Projetos-sgr`) fica obsoleto a partir de agora.
