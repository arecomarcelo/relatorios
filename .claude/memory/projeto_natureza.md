---
name: projeto-natureza
description: "Natureza do projeto SGR — sistema legado monolítico já em produção, fora da esteira de extração SGA 00-06; não requer % Desenvolvido/Planejamento"
metadata:
  node_type: memory
  type: project
  originSessionId: b7e04927-9c7f-4360-8285-1c4e23ff3997
---

O SGR (`/media/areco/Backup/Oficial/Projetos/nova-estrutura/sgr` — movido de `/media/areco/Backup/Oficial/Projetos/sgr` em 03/08/2026, ver [[projeto_movido_nova_estrutura]]) é o sistema legado monolítico (Streamlit + Django ORM) que já está em produção, conectando diretamente ao banco `sga` nativo (host `195.200.1.244`, mesmo banco de onde o `03-clonar-banco-sga` espelha dados para o `sga_multiapp`). Não foi criado pelas skills `00-gerar-planejamento`/`01-iniciar-projeto` da esteira de extração SGA (Hostinger) nem pertence à esteira `hauxtech`.

**Decisão confirmada com o usuário em 17/07/2026 (sessão via Claude Code, Note_Oficial):** o protocolo global de Finalizar Sessão (atualizar/criar documento de Planejamento com % Desenvolvido) **não se aplica ao SGR** — é sistema legado já em produção, não projeto novo em desenvolvimento incremental. Pular essa etapa em toda sessão futura do SGR, sem perguntar de novo.

**Como aplicar:** ao rodar o protocolo "Finalizar Sessão" neste projeto, pular a etapa de % Desenvolvido/Planejamento e não criar `documentacao/Planejamento SGR.md`. Também não é esperado registro em `apps.conf`/`Score Implantacao.md` (esses são exclusivos dos ecossistemas hauxtech/oficial com Score centralizado).
