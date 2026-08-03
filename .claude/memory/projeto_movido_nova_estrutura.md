---
name: projeto-movido-nova-estrutura
description: "Histórico: SGR foi movido de Projetos/sgr para Projetos/nova-estrutura/sgr em 03/08/2026 (venv recriada) e, na mesma data, renomeado para Projetos/nova-estrutura/relatorios — ver projeto_renomeado_relatorios para o rename"
metadata:
  type: project
  originSessionId: sessao-2026-08-03-note-oficial
---

Em 03/08/2026 (Note_Oficial, via Claude Code), a pedido do usuário, o projeto foi movido de `/media/areco/Backup/Oficial/Projetos/sgr` para `/media/areco/Backup/Oficial/Projetos/nova-estrutura/sgr` (mesma partição, `mv` simples — `nova-estrutura` já existia como pasta guarda-chuva das apps extraídas do ambiente Oficial: administracao, comex, estoque, multi-financeiro, rh etc.). **Ainda na mesma data**, o projeto foi renomeado de `sgr` para `relatorios` (ver [[projeto_renomeado_relatorios]]) — caminho final: `/media/areco/Backup/Oficial/Projetos/nova-estrutura/relatorios`.

**O que foi ajustado (na movimentação de pasta):**
- `venv/` recriada do zero no novo caminho (continha paths absolutos hardcoded em `pyvenv.cfg`, `activate*` e shebangs de `venv/bin/*` — não é portável entre caminhos).
- Descoberto e corrigido efeito colateral pré-existente: 24 arquivos de `venv/bin/` estavam rastreados pelo git apesar de `venv/` já estar no `.gitignore`. Rodado `git rm -r --cached venv`.
- Nenhuma outra dependência de caminho absoluto encontrada: `.env`, `.streamlit/secrets.toml`, `app/settings.py` (`BASE_DIR` via `Path(__file__)`) e `core/logging_config.py` (`Path("logs")` relativo) já eram portáveis.
- Validado com `python manage.py check` (Django OK) e imports de `streamlit`/`django` na venv nova.

**Pendências conhecidas (da movimentação, ainda não revisitadas):**
- Existe uma pasta `sgr (cópia)` em `/media/areco/Backup/Oficial/Projetos/` (mesma data de modificação da pasta original) — não foi tocada, não se sabe sua origem/propósito; não presumir que é lixo a remover sem perguntar ao usuário.
- A origem exata do hook de auto-commit (ver [[projeto_autocommit]]) não foi localizada.

**Como aplicar:** o caminho canônico do projeto agora é `/media/areco/Backup/Oficial/Projetos/nova-estrutura/relatorios` (não mais `.../sgr`). Esta memória (e as demais do projeto) foi migrada para o diretório de memória canônico correspondente ao novo nome (`~/.claude/projects/-media-areco-Backup-Oficial-Projetos-nova-estrutura-relatorios/memory/`); os diretórios antigos (`-media-areco-Backup-Oficial-Projetos-sgr` e `-media-areco-Backup-Oficial-Projetos-nova-estrutura-sgr`) ficam obsoletos a partir de agora.
