---
name: projeto-natureza
description: "Natureza do projeto Relatórios (antigo SGR) — sistema legado monolítico; a exceção histórica de não criar Planejamento foi supersedida pelo protocolo global em 29/09/2026"
metadata:
  node_type: memory
  type: project
  originSessionId: b7e04927-9c7f-4360-8285-1c4e23ff3997
---

O Relatórios (antigo SGR, ver [[projeto_renomeado_relatorios]] — renomeado em 03/08/2026; caminho `/media/areco/Backup/Oficial/Projetos/nova-estrutura/relatorios`, movido de `/media/areco/Backup/Oficial/Projetos/sgr` também em 03/08/2026, ver [[projeto_movido_nova_estrutura]]) é o sistema legado monolítico (Streamlit + Django ORM) que já está em produção, conectando diretamente ao banco `sga` nativo (host `195.200.1.244`, mesmo banco de onde o `03-clonar-banco-sga` espelha dados para o `sga_multiapp`). Não foi criado pelas skills `00-gerar-planejamento`/`01-iniciar-projeto` da esteira de extração SGA (Hostinger); é um app do ecossistema **oficial**, sem ser produto HauxTech.

**Decisão histórica confirmada com o usuário em 17/07/2026 (sessão via Claude Code, Note_Oficial):** à época, a exceção ao protocolo era manter o SGR legado sem Planejamento/% Desenvolvido, por já estar concluído e em produção.

**Atualização 29/09/2026 (VPS via Hermes VPS):** o protocolo global atual de Finalizar Sessão determina criar Planejamento com linha `GERAL` quando ausente e acompanhar o percentual também em apps existentes; para apps oficiais com Score centralizado, exige o registro em `apps.conf` e no Score. Isso supersede a exceção histórica para novos escopos. No SGR, manter o plano incremental explicitamente delimitado para não reclassificar o escopo histórico concluído; preservar a distinção entre este legado Streamlit e `relatorios-novo` (extração Django).
