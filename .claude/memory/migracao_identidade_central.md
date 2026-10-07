---
name: migracao-identidade-central
description: "CONCLUÍDA em produção (27/08/2026): migração da autenticação/permissões do Relatórios do sga legado para a identidade central do administracao (oficial_db) — todos os 5 gates executados e validados"
metadata: 
  node_type: memory
  type: project
  originSessionId: b62d7137-ec19-4bc4-84fe-922a72ba08ac
  modified: 2026-08-27T12:46:19.898Z
---

Substitui gradualmente o comportamento descrito em [[projeto_permissoes]] (autenticação
própria contra `sga`/`auth_*`, bypass hardcoded `username == "admin"`). Ver plano completo
em `/home/areco/.claude/plans/virtual-squishing-sparrow.md`.

**Escopo confirmado com o usuário:** o Relatórios NÃO é tratado como as demais 9 apps do
ecossistema oficial — não tem schema próprio no `oficial_db` (não é dono de nenhuma
tabela; dados de negócio já migrados para `oficial_db` por outra frente, espalhados pelos
schemas de `estoque`/`cobranca`/`financeiro`/`comex`/`compartilhado`/`nao_classificado` —
fora do escopo desta migração). Aqui só identidade e permissão: cadastro no
`administracao` (`AppRegistrada`), concessão de acesso (`AcessoApp`) e visibilidade de
menu por usuário (`ModuloMenu`/`AcessoModuloMenu`), com a checagem real dentro do
Relatórios passando a consultar essas tabelas centrais em vez do `sga`.

**Descoberta importante:** o "formulário para dar permissão às funções da app" que o
usuário pediu **já existe e é genérico** — `AppAcessoView`/`UsuarioAcessoView`/
`AcessoModuloMenuView` em `administracao/apps/administracao/views.py` — não foi
necessário criar tela nova, só popular os dados (`AppRegistrada`+`ModuloMenu`) para o
Relatórios funcionar com elas.

**Mapeamento de usuários (legado `sga` → identidade central), todos confirmados em
produção:** `admin`→`admin` (superusuário), `areco`→`areco`, `desenv`→`desenv`,
`isabella`→`comex01`, `leticia`→`marketing02` (confirmado existente em produção em
27/08/2026, apesar de ausente no dev local — dev não tem todos os usuários de prod),
`teste`→não migrado (decisão explícita do usuário).

**Estado final em 27/08/2026 — CONCLUÍDA em produção, todos os 5 gates executados:**
1. ✅ `marketing02` confirmado em `administracao.auth_user` de produção antes de prosseguir.
2. ✅ `registrar_app_relatorios` + `conceder_acesso_relatorios` rodados em produção
   (via `docker exec` no container `administracao_web`, sem rebuild de imagem — o código
   dos 2 commands foi ao ar via deploy padrão do `administracao` ANTES, ver abaixo).
3. ✅ Provisionamento (`ProvisionamentoService`) executado contra o `oficial_db` de
   produção — role `relatorios_user` criado com `GRANT SELECT` nas 5 tabelas centrais;
   senha real gerada e gravada no `.env` de produção do Relatórios (`OFICIAL_DB_*`).
4. ✅ `oficial_db_net` adicionada ao `stack.yml` do Relatórios; deploy completo (`git push`
   + build/push da imagem + `docker stack deploy`) executado com sucesso.
5. ✅ Validado dentro do container `relatorios_web` em produção: os 5 usuários mapeados
   são encontrados em `administracao.auth_user` e a checagem de senha roda corretamente
   contra o banco real (testado com senha propositalmente errada, sem expor senha real).

**Deploy também executado no `administracao`** (pré-requisito da Fase 2/3): os 2
management commands só existiam localmente — precisaram de um deploy completo do
`administracao` (push + build + `docker stack deploy`) antes de poderem rodar em
produção via `docker exec`.

**Gotcha de execução (útil para próximas sessões com SSH remoto):** `$(...)`/variáveis
dentro de uma string **duplamente** citada (`ssh host "... $(cmd) ..."`) são expandidos
pelo shell **local**, não no host remoto — precisa escapar (`\$(cmd)`) ou, mais seguro,
usar aspas **simples** na string externa (`ssh host '... $(cmd) ...'`) para garantir
expansão no remoto. Um deslize nisso fez uma senha gerada em produção ser perdida antes
de ser gravada no `.env` (sem corromper nada — só precisou gerar outra).

**Pendências conhecidas, fora do escopo desta migração:**
- `.env` de dev local (`sga_db_local`, porta 5440) não tem os usuários `comex01`/
  `marketing02` sincronizados de produção — só `admin`/`areco`/`desenv`/`comex01` existem
  lá hoje; útil saber para não reconferir do zero numa sessão futura.
- Senhas de teste temporárias (`teste123`) foram definidas para `admin`/`areco`/`desenv`
  **no dev local apenas**, durante a validação — se esse ambiente for usado por outra
  pessoa/finalidade, considerar resetar.
- `UserService`/`UserRepository` (raiz do Relatórios, baseados no `sga`) foram mantidos
  intactos como caminho de rollback — não apagar sem necessidade.

**Como aplicar:** ver [[projeto_permissoes]] — atualizada para refletir este novo
comportamento definitivo (fonte de identidade/permissão agora é a central, não mais o
`sga`).
