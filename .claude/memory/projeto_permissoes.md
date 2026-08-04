---
name: projeto-permissoes
description: "Arquitetura real do sistema de permissões do Relatórios (antigo SGR) — checagem só no menu, banco auth_* compartilhado entre múltiplos apps Django, sem re-checagem no router"
metadata:
  node_type: memory
  type: project
  originSessionId: b7e04927-9c7f-4360-8285-1c4e23ff3997
  modified: 2026-08-04T14:03:16.212Z
---

O Relatórios (antigo SGR, ver [[projeto_renomeado_relatorios]]) usa o sistema de auth padrão do Django (tabelas `auth_user`, `auth_group`, `auth_permission`, etc.), mas com particularidades importantes descobertas em 17/07/2026:

- **Checagem só existe no menu** (`apps/auth/modules.py`, função `_check_permission`), comparando o `codename` da permission contra `st.session_state.permissions` (lista carregada uma única vez no login, em `apps/auth/views.py:131`, e nunca recarregada durante a sessão). As telas (`pedidos.py`, `vendas/views.py`) e o roteador principal (`app.py::main()`) **não refazem a checagem** — `main()` só olha `st.session_state.current_module`, sem validar permissão. Ou seja, a proteção é só cosmética no menu; não há gate real por tela.
- **Bypass hardcoded**: `username == "admin"` libera tudo em `_check_permission` (não é baseado em `is_staff`/`is_superuser`).
- **Banco de permissões compartilhado entre vários apps Django distintos** que usam o mesmo Postgres (`sga`, host `195.200.1.244`): existem `ContentType`s duplicados para o model "venda" sob `app_label` diferentes (`app`, `vendas`, `entidades`, `dashboard`), pois cada app Django do ecossistema registra seu próprio `app_label`. Como a checagem em `repository.py` (linhas 33-60) só compara o `codename` da permission via SQL raw nas tabelas `auth_*`, **ignorando completamente o `content_type`**, uma permission de qualquer app_label satisfaz a checagem — não há isolamento por app.
- **Não existe app Django `app.py` de admin customizado** (nenhum `admin.py` no projeto) — o Django Admin (`/admin/`) só expõe Users e Groups (registro automático do `django.contrib.auth`), sem página própria de "Permissions" (só aparece dentro do multi-select de User/Group).
- **Não há tela própria no Relatórios para atribuir permissões a usuários/grupos** — precisa ser feito via Django Admin (`/admin/`) ou diretamente nas tabelas `auth_user_user_permissions`/`auth_group_permissions`.

**Como aplicar:** ao criar uma nova permission granular (como foi feito com `view_pedido` para Vendas > Pedidos, e `view_comparativo` para Vendas > Comparativo em 04/08/2026), lembrar que (1) não precisa gerar migração — o app `app` nunca teve pasta de migrations, então criar `ContentType`+`Permission` direto via `manage.py shell` é o padrão já usado e aceito (reaproveitar o `ContentType` app_label=`app`/model=`venda`, id 213, já usado pelas permissions granulares deste projeto); (2) atualizar `apps/auth/modules.py` em DOIS lugares — o `permission` do sub-item (troca isolada) E o `permission` (lista OR) do módulo GRUPO pai, senão um usuário só com a nova permission nem vê o grupo para chegar no sub-item; (3) permissions são atribuídas diretamente a usuários (`auth_user_user_permissions`), não a grupos Django — não há tela própria no Relatórios, só via `/admin/` ou shell; (4) avisar o usuário que não há re-checagem em `app.py`, então mudanças de permissão só afetam o que aparece no menu, não um bloqueio real de acesso direto à tela.

**Permissions granulares já criadas neste projeto:** `view_pedido` (Vendas > Pedidos, id 743), `view_comparativo` (Vendas > Comparativo, id 744, criada 04/08/2026 — ninguém atribuído ainda, decisão explícita do usuário de conceder depois manualmente via `/admin/`).
