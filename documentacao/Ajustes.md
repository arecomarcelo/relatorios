---
title: Ajustes do Projeto Relatórios
description: Registro de alterações e commits do projeto Oficial Relatórios.
version: 1.0.0
status: Oficial
owner: Oficial Sport
authors:
  - Marcelo Areco
created: 2026-09-30
updated: 2026-09-30
---

# Ajustes do Projeto Relatórios

### **08:44 - Commit 1 (VPS via Hermes VPS) — Publicação da automação diária e regularização da sincronização**
- Preservadas e publicadas as memórias, o planejamento incremental, os scripts da automação diária, os testes e o ajuste do `predeploy.sh`.
- Validações realizadas: `git diff --check`, `bash -n scripts/predeploy.sh`, sintaxe de cinco arquivos Python e nove testes manuais do runner.
- A suíte pytest permanece dependente de `venv` e das versões declaradas em `requirements.txt`; nenhum pacote foi instalado na VPS.
- Realizado em Hermes VPS Hostinger via Hermes VPS.

### **08:52 - Commit 2 (VPS via Hermes VPS) — Confirmação da publicação da automação diária**
- Atualizado o histórico para registrar que o commit autorizado da automação diária foi publicado e confirmado em `origin/main`.
- Validação final do runner mantida em 9 casos manuais aprovados; pytest segue dependente de ambiente futuro com `venv`.
- Realizado em Hermes VPS Hostinger via Hermes VPS.

### **16:39 - Commit 3 (Note_Oficial via Claude Code) — Correção do UnicodeEncodeError no logging**
- Causa raiz: `django.setup()` roda a cada rerun do Streamlit e reaplica `settings.LOGGING`, cujo `FileHandler` não tinha `encoding`; com o fallback `setlocale(LC_ALL, "C")` (o container não tem `pt_BR.UTF-8`) o arquivo abria em ASCII e o "✓" falhava (22 ocorrências/24 h).
- `app/settings.py`: `"encoding": "utf-8"` no handler `file`; views de estoque/boletos/clientes/extratos com fallback `"C.UTF-8"`.
- Teste de regressão `tests/test_logging_encoding.py` (falhou antes com o mesmo erro de produção; 15/15 depois). Deploy às 16:46, validado: container `healthy` e 0 erros após a subida.
- Commit `fbbf2c43`. Realizado em Note_Oficial via Claude Code.

### **17:02 - Commit 4 (Note_Oficial via Claude Code) — Keep-alive, mypy e formatação**
- `app.py`: keep-alive só roda fora do deploy Docker (`SGR_DOCKER_DEPLOY`) — no VPS pingava a URL antiga do Streamlit Cloud (404) e abria uma thread infinita por sessão.
- `mypy.ini`: `explicit_package_bases = True` — o mypy via `scripts/` sob dois nomes de módulo e abortava; `predeploy.sh` voltou a 0 erros.
- Formatação do padrão do projeto em `scripts/daily_sales_preview.py`, `scripts/daily_sales_report_runner.py` e `tests/test_daily_sales_report_runner.py`.
- Deploy às 17:07, validado. Commit `72f029c9`. Realizado em Note_Oficial via Claude Code.

### **17:16 - Commit 5 (Note_Oficial via Claude Code) — Registro dos ajustes da sessão**
- Inclusão retroativa dos Commits 3 e 4 neste documento (não registrados antes dos commits). Realizado em Note_Oficial via Claude Code.

### **10:20 - Commit — Limite de memória (auditoria Hostinger, Fase 6, onda 1)**
- `stack.yml`: `deploy.resources.limits.memory` em `web` 704 MiB — pico de 7 dias (30/09–07/10/2026, cAdvisor/Prometheus) × 1,5, arredondado para múltiplo de 64 MiB.
- Objetivo: impedir que um processo descontrolado consuma a RAM do host compartilhado. Cobertura: alertas `MemoriaPertoDoLimite` (> 90% por 10 min) e `ContainerOOM` no Prometheus.
- Detalhes no Plano de Correção da auditoria Hostinger v1.1.0 (`hauxtech-documentacao`).

Realizado em Note_Oficial via Claude Code.

### **11:03 - Commit (Note_Oficial via Claude Code) — Reconciliação das memórias e ativação do hook**
- Na Note_Oficial o `core.hooksPath` não estava ativo e as memórias da pasta canônica e do repositório divergiam nos dois sentidos. Reconciliadas (backup dos dois lados antes):
  - `projeto_permissoes.md`: mantida a versão canônica de 27/08/2026 (identidade central), que substitui a do repositório (25/08, sistema antigo).
  - `projeto_natureza.md` e `automacao_relatorios_diarios.md`: versões do repositório (29–30/09/2026) levadas à pasta canônica.
  - `migracao_identidade_central.md`: existia só na pasta canônica; agora versionada.
  - `projeto_divergencia_main_20260805.md`: existia no repositório sem entrada no índice; incluída no `MEMORY.md`.
  - `logging_encoding_bug.md`: atualizada com a causa raiz real corrigida em 06/10/2026 (`fbbf2c43`).
- Removidas do repositório 4 memórias do `relatorios-novo` copiadas aqui por engano no commit `76520dc4` (`projeto_banco_permissoes`, `projeto_planejamento`, `projeto_scaffolding`, `projeto_tabulator_gotchas`) — cópias idênticas permanecem no `relatorios-novo`.
- `git config core.hooksPath .githooks` ativado na Note_Oficial; pasta canônica e espelho idênticos (16 arquivos).
- ⚠️ Pendente na Note_Casa: conferir se a pasta canônica do `relatorios` lá ainda tem essas 4 memórias e removê-las antes do próximo commit, senão o `pre-commit` as traz de volta.
