---
name: projeto-banco-permissoes
description: "Fase 1 (atual): banco nativo sga + permissões do sga legado. Fase 2 (futura, PÓS-MVP): migrar para sga_multiapp — AJUSTAR PERMISSÕES NESSA MIGRAÇÃO, pedido explícito do usuário para lembrar"
metadata: 
  node_type: memory
  type: project
  originSessionId: be175a86-c6b1-4924-93fb-8e68952ceeb1
  modified: 2026-07-22T22:21:30.202Z
---

Decidido com o usuário em 22/07/2026, em duas fases explícitas:

**Fase 1 (esta leva, MVP)**: a app conecta direto no **banco nativo `sga`** — a mesma fonte que
o SGR (Streamlit) usa hoje. Isso vale tanto para os dados de negócio (`Vendas`, `Vendedores`,
`Produtos`, `VendaPagamentos`, `VendaProdutos`, `OS`, `OS_Produtos`, `RPA_Atualizacao`) quanto
para **autenticação/permissões** (`auth_user`/`auth_group`/`auth_permission` do `sga` nativo,
não do `sga_multiapp`). Diferente do padrão das demais apps Oficial já extraídas
(`administracao`/`financeiro`/`estoque`/`comex`), que leem do mirror `sga_multiapp`/schema
próprio.

**Fase 2 (PÓS-MVP, sem data definida — item US-PM.005 no Backlog)**: migrar a fonte de dados
para `sga_multiapp` (mirror, schema `relatorios` próprio, via skill `03-clonar-banco-sga`),
alinhando com o padrão das demais apps.

**⚠️ AJUSTE PENDENTE — PEDIDO EXPLÍCITO DO USUÁRIO PARA LEMBRAR NESSA MIGRAÇÃO FUTURA**: ao
migrar de `sga` nativo para `sga_multiapp` (Fase 2), a camada de **autenticação/permissões**
também precisa ser revisada e adaptada para apontar para a base de usuários do `sga_multiapp` —
isso **não** acontece automaticamente só migrando as tabelas de dado de negócio. Sem esse ajuste,
usuários podem deixar de conseguir logar ou perder permissões após a migração de banco.

**Como aplicar**: antes de iniciar a Fase 2 (qualquer sessão futura que for rodar
`03-clonar-banco-sga` para esta app), checar explicitamente com o usuário como tratar a camada
de auth/permissões — não assumir que é só trocar a connection string. Ver também
[[projeto-planejamento]] (Blueprint §Estratégia de Banco de Dados),
[[projeto-natureza]] e [[projeto-scaffolding]].

**Gotcha real (22/07/2026, testado no scaffolding)**: `.env` local aponta `DB_HOST` para o IP
público da VPS Hostinger (mesmo padrão do `.env.example` do SGR legado). Com `DB_PASSWORD` ainda
como placeholder, o erro observado foi `FATAL: password authentication failed` **e**
`no pg_hba.conf entry for host ...` na mesma mensagem — mas depois que o usuário preencheu a
senha real, a conexão funcionou de primeira a partir de Note_Casa (`migrate --check` sem erro,
`runserver` respondendo em todas as rotas testadas). Ou seja, **o IP de Note_Casa já estava
liberado em `pg_hba.conf`** — a mensagem de `pg_hba` no teste anterior era só ruído da tentativa
de autenticação já rejeitada por senha errada, não um bloqueio de IP real. Se uma máquina
**diferente** (Note_Oficial/Jarvis) apresentar esse mesmo erro com a senha já correta, aí sim
vale investigar `pg_hba.conf` de verdade.
