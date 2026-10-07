---
name: projeto-permissoes
description: "Arquitetura atual do sistema de permissões do Relatórios — desde 27/08/2026, identidade e autorização vêm da identidade central (administracao/oficial_db), não mais do sga legado; checagem ainda só no menu, sem re-checagem no router"
metadata: 
  node_type: memory
  type: project
  originSessionId: b62d7137-ec19-4bc4-84fe-922a72ba08ac
  modified: 2026-08-27T12:46:50.095Z
---

**Desde 27/08/2026** (ver [[migracao_identidade_central]] para o histórico completo da
migração), o Relatórios autentica e resolve permissões contra a **identidade central**
do ecossistema oficial — schema `administracao`, banco `oficial_db` — a mesma fonte já
usada pelas outras 9 apps do ecossistema. Isso substitui o comportamento antigo (auth
próprio contra `sga`/`auth_*`, descrito no histórico abaixo).

**Como funciona hoje:**
- `apps/auth/central_repository.py` (conexão psycopg2 dedicada, `OFICIAL_DB_*` no `.env`,
  rede `oficial_db_net`) + `apps/auth/central_auth_service.py::CentralAuthService.
  validate_user()` fazem: usuário existe em `administracao.auth_user`? Senha bate
  (`check_password`)? Superusuário central → bypass total (**não é mais** o hardcode
  `username == "admin"`). Usuário comum → precisa de `AcessoApp` (app "relatorios") →
  `AcessoModuloMenu` decide quais dos 12 módulos ficam visíveis (nenhuma linha = sem
  restrição, vê tudo).
- `apps/auth/views.py` (login) grava `st.session_state.is_superuser` além de
  `st.session_state.permissions` (lista de codenames, mesmo formato de sempre).
- `apps/auth/modules.py::_check_permission` continua comparando codename contra
  `st.session_state.permissions` — **zero mudança nessa lógica**, só o bypass de admin
  passou a checar `is_superuser` em vez do username.
- **Checagem ainda só existe no menu** — `app.py::main()` continua sem re-checagem por
  tela (limitação antiga, não resolvida por esta migração).
- Dados de negócio (vendas, estoque, boletos etc.) continuam 100% no `sga` legado, sem
  nenhuma mudança — só identidade/permissão migrou.
- `UserService`/`UserRepository` (raiz, baseados no `sga`) foram mantidos intactos como
  caminho de rollback rápido — não apagar sem necessidade.

**Catálogo de módulos (`ModuloMenu`, schema `administracao`) → codename**, os mesmos 13
de sempre: `produtos`→`view_produtos`, `boletos`→`view_boletos`,
`extratos`→`view_extratos`, `comercial`→`view_venda` (+ `change_venda` global via
`AcessoApp.pode_editar`), `pedidos`→`view_pedido`, `comparativo`→`view_comparativo`,
`campanha_adwords`→`view_campanhas`, `campanha_meta`→`view_campanha_meta`,
`recebimentos`→`view_recebimentos`, `clientes`→`view_clientes`, `comex`→`view_comex`,
`ordem_servico`→`view_os`.

**Como conceder/revogar acesso agora:** via as telas **já existentes** no `administracao`
— `AppAcessoView`/`UsuarioAcessoView` (concede `AcessoApp`, com o link "Módulos" levando a
`AcessoModuloMenuView`, que lista os 12 módulos como checkboxes). **Não usar mais**
`/admin/` do Relatórios nem `auth_user_user_permissions` do `sga` para isso — só afeta o
sistema antigo, que não é mais consultado no login.

**Mapeamento de usuários (username no `sga` → username na identidade central), estado
atual (27/08/2026):** `admin`→`admin` (superusuário), `areco`→`areco`, `desenv`→`desenv`,
`isabella`→`comex01`, `leticia`→`marketing02`, `teste`→não migrado (sem acesso).
Visibilidade de módulo por usuário replicada fielmente do estado antigo — ver
[[migracao_identidade_central]] para a tabela completa.

---

## Histórico — sistema antigo (sga legado, válido até 26/08/2026, mantido como rollback)

O Relatórios (antigo SGR, ver [[projeto_renomeado_relatorios]]) usava o sistema de auth padrão do Django (tabelas `auth_user`, `auth_group`, `auth_permission`, etc.) do banco `sga`, com particularidades importantes descobertas em 17/07/2026:

- **Checagem só existe no menu** (`apps/auth/modules.py`, função `_check_permission`), comparando o `codename` da permission contra `st.session_state.permissions` (lista carregada uma única vez no login, e nunca recarregada durante a sessão). As telas e o roteador principal (`app.py::main()`) **não refazem a checagem**.
- **Banco de permissões compartilhado entre vários apps Django distintos** que usam o mesmo Postgres (`sga`, host `195.200.1.244`): existem `ContentType`s duplicados para o model "venda" sob `app_label` diferentes (`app`, `vendas`, `entidades`, `dashboard`). A checagem em `repository.py` só compara o `codename` via SQL raw, **ignorando completamente o `content_type`** — não há isolamento por app.
- **Não existe app Django `admin.py` customizado** — o Django Admin (`/admin/`) só expõe Users e Groups.

**Permissions granulares criadas neste projeto (codenames, ainda válidos no novo sistema):** `view_pedido` (id 743), `view_comparativo` (id 744), `view_campanhas`/`change_campanhas` (id 745/746), `view_campanha_meta`/`change_campanha_meta` (id 747/748). Ver [[projeto_dashboard_campanhas]].

**Estado de atribuição em produção no sistema antigo (checado em 25/08/2026, histórico — não reflete mais o comportamento real desde 27/08/2026):** `admin` sempre via tudo (bypass hardcoded). `leticia` tinha `view_campanhas`+`view_campanha_meta`. `areco` tinha só `view_campanhas`. Essa distribuição foi a base do mapeamento replicado na migração — ver seção acima.
