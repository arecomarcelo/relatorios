---
name: projeto-scaffolding
description: "01-iniciar-projeto concluído em 22/07/2026 — scaffolding Django completo, decisões de escopo (deploy e Chamados pulados), estado atual das apps e pendências para rodar localmente"
metadata: 
  node_type: memory
  type: project
  originSessionId: be175a86-c6b1-4924-93fb-8e68952ceeb1
  modified: 2026-07-22T22:21:16.322Z
---

Skill `01-iniciar-projeto` executada em 22/07/2026 (Note_Casa, Claude Code). Projeto já era a
raiz (`/home/areco/Projetos/Oficial/relatorios`, mesmo padrão sem prefixo `multi-` de
`estoque`/`comex`/`administracao`) — nenhuma subpasta criada.

**Decisões de escopo confirmadas com o usuário (via AskUserQuestion) antes de rodar a skill:**
1. **Pular infraestrutura de deploy** (PASSOs 11/11b-11f/13c da skill: `docker-compose.prod.yml`,
   `stack.yml` Swarm, CI/CD GHCR, Docker Secrets, instrumentação Prometheus, registro em
   `AppRegistrada`, registro no Score de Implantação) — alinhado ao PRD/Blueprint, que já diziam
   explicitamente "deploy fica para quando as skills 02/03/04 rodarem". Retomar nessa ocasião.
2. **Pular Kanban de Chamados** na Home (PASSO 12f item 2 da skill) — o model vive no schema
   `compartilhado` do `sga_multiapp`, mas esta leva conecta só no `sga` nativo (ver
   [[projeto-banco-permissoes]]). Home nasceu só com cards de navegação para os 5 módulos.
3. **Criar repositório privado no GitHub** já nesta etapa.

**O que foi criado:**
- `config/settings/{base,development,production,hostinger}.py` via `python-decouple`. O stub
  `config/settings.py` (raiz) do PASSO 6 da skill foi **removido** — coexistir com o pacote
  `config/settings/` é logicamente impossível (testado empiricamente: o pacote sempre vence a
  resolução de import do Python; o stub nunca seria executado). **Se outra sessão for rodar essa
  mesma skill em outro projeto, vale o mesmo alerta** — não recriar esse stub.
- `apps/core` (health `/health/`, páginas de erro 400/403/404/500, `HomeView` = dashboard de
  navegação para os 5 módulos, context processor de footer), `apps/accounts` (login/logout
  **direto** contra `auth_user` do `sga` nativo — sem backend customizado, `ModelBackend` padrão
  do Django é suficiente, diferente do padrão de identidade centralizada usado por
  `multi-financeiro`/`multi-ai`, que não se aplica aqui por causa da Fase 1 no `sga` nativo).
- `apps/{estoque,vendas,recebimentos,comex,sac}` — só scaffolding (URL + view + template
  placeholder "em implementação"). Dados reais (queries sobre `Produtos`/`Vendas`/etc.) são as
  Fases 1-5 do `documentacao/Plano de Implementação 01.md`, ainda não feitas.
- Padrão visual `.os-*` integrado **direto** (não via `09-aplicar-padrao-visual-oficial` como
  migração posterior — Blueprint já previa isso). `os.css`, `base.html`, template de login e
  páginas de erro adaptados a partir da referência `multi-financeiro` (piloto do padrão).
  Tabulator.js + `static/css/tabulator-dark.css` + HTMX integrados ao `base.html` via CDN — SP00
  do Plano de Sprints (`planejamento/04 - sprints.md`) ficou 100% concluído nesta sessão.
- Banner "Em Desenvolvimento" (padrão global do CLAUDE.md, Bootstrap+Dracula) **não** foi
  replicado — confirmado por observação direta em `multi-financeiro`/`multi-ai` que nenhuma app
  `.os-*` em produção implementa esse banner; a exigência do CLAUDE.md global está escopada às
  apps hauxtech (Bootstrap 5.3) e Next.js (Tailwind), não ao padrão `.os-*` do ambiente Oficial.
- `documentacao/Plano de Implementação 01.md` — fases derivadas 1:1 de
  `planejamento/04 - sprints.md` (SP00-SP05), % Desenvolvido inicial calculado em **17% (4/23
  etapas)** — só a Fase 0/Setup está concluída. Deploy (Fase 6) fica fora do denominador do %
  (PÓS-MVP, fora do escopo desta leva).
- `Dockerfile` simples (sem `entrypoint.sh`/advisory lock — isso é PASSO 11c, parte da infra de
  deploy adiada). Sem `docker-compose.yml`/`stack.yml` nesta leva.
- Infra de sync de memória (`scripts/claude-sync-{push,pull}.sh`, `.githooks/{pre-commit,
  post-merge,post-checkout}`, `core.hooksPath` configurado) copiada de `multi-financeiro`.

**Testado e validado:**
- `manage.py check` sem erros.
- Usuário preencheu `DB_PASSWORD` real no `.env` ainda nesta sessão — conexão com o banco `sga`
  nativo confirmada (`migrate --check` sem erro; `auth_user` já tem 30 usuários, incluindo
  superusuário `admin`, compartilhado com o SGR legado). IP da máquina de dev (Note_Casa) já
  estava liberado em `pg_hba.conf` — não precisou de ajuste.
- `runserver` local testado de ponta a ponta: `/health/` → 200, `/` deslogado → 302 (login),
  `/accounts/login/` → 200, `/estoque/` deslogado → 302 (`LoginRequiredMixin` funcionando).

**Pendências restantes:**
1. `python manage.py createsuperuser` — opcional, já existe `admin` superusuário no `sga`.
2. Começar a Fase 1 (Estoque/SP01) do Plano de Implementação — próximo passo real do projeto.

Ver também [[projeto-natureza]], [[projeto-planejamento]] e [[projeto-banco-permissoes]].
