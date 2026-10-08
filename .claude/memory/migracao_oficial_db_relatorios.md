---
name: migracao-oficial-db-relatorios
description: Relatórios migrado para o oficial_db no branch migracao-oficial-db (etapa 29 do plano de migração RPA, 08/10/2026) — não publicar antes do corte coordenado da Onda 3
metadata:
  type: project
---

Em 08/10/2026 (sessão do guarda-chuva multi-aplicacao) o Relatórios foi migrado do legado `sga` para o `oficial_db` no **branch `migracao-oficial-db`** — etapa 29 do `Plano de Implementação - Migração RPA para Oficial DB` (multi-aplicacao). O `main` continua lendo o legado e é o que está em produção.

- Só leitura, sem schema próprio: SQL, models (`app/models.py`) e `fetch_data` (`SCHEMA_POR_TABELA` em `repository.py`) usam nomes qualificados — `vendas` (Vendas, VendaPagamentos, VendaProdutos, Vendedores, VendaConfiguracao, VendaFormaPagamento, OS, OS_Produtos), `compartilhado` (Clientes, PessoaTipos, Produtos), `financeiro` (Extratos, Bancos, Empresas, CentroCustos), `cobranca` (BoletosEnviados).
- A data de atualização de Vendas/SAC vem de `rpa."ControleAtualizacao"` (RPA 7/9), mantendo as colunas Data/Hora/Periodo/Inseridos/Atualizados.
- Defaults sem IP de produção (`oficial_db`/`relatorios_user`/`localhost`); `search_path` de defesa via `DB_SCHEMA`, sem `nao_classificado`; `stack.yml` sem `extra_hosts`.
- Os GRANTs do `relatorios_user` ficam em `multi-aplicacao/scripts/grants_relatorios_oficial_db.sql`. Hoje, em produção, ele só tem SELECT em `administracao`.

**Why:** a Onda 3 desliga a escrita no legado. Achado: o `Extratos` do legado está parado em 10/10/2024, então hoje a tela de Extratos mostra dados velhos (o oficial vai até 30/04/2026).

**How to apply:** não fazer merge/deploy do branch antes da etapa 32 (pré-requisitos na etapa 32 do plano). Para testar no local, use `SGR_DOCKER_DEPLOY=1` e `DB_*` exportados: existe `.streamlit/secrets.toml` com credenciais, e o `.env` aponta para o legado de produção. `repository.py` e `service.py` são CRLF; preserve o fim de linha ao editar.

Realizado em Note_Oficial via Claude Code.
