---
name: projeto-autocommit
description: "O repositório Relatórios (antigo SGR) tinha um hook externo que auto-commitava com mensagens \"Commit N\" — confirmado INATIVO desde 04/08/2026 (pós-rename); commits agora são sempre manuais"
metadata:
  node_type: memory
  type: project
  originSessionId: b7e04927-9c7f-4360-8285-1c4e23ff3997
  modified: 2026-08-04T14:23:04.788Z
---

Observado em 17/07/2026: alterações feitas em arquivos do projeto (ex.: `apps/vendas/pedidos.py`, `Historico.md`) foram commitadas e enviadas ao `origin/main` automaticamente por um processo externo à sessão do Claude Code — sem que o comando `git commit`/`git push` tivesse sido executado nesta conversa. O commit apareceu com mensagem genérica sequencial ("Commit 148", seguindo commits anteriores "Commit 147", "Commit 146"...) e também atualizou sozinho `documentacao/recursos/Ajustes.md` com uma entrada no formato `##### hh:mm - Commit nnn`.

Isso bate com o padrão descrito no CLAUDE.md global (predeploy/hook que atualiza `Ajustes.md` e faz auto-commit), mas aqui parece disparar por simples alteração de arquivo (save), não só no ciclo de deploy.

**Como aplicar:** antes de rodar `git add`/`git commit`/`git push` manualmente neste projeto, sempre rodar `git status`/`git log --oneline -3` primeiro — é bem possível que o hook já tenha commitado e feito push sozinho, tornando a ação manual redundante (ou gerando confusão se tentar commitar algo que já foi commitado). Não tentar "desfazer" ou alterar esse hook sem pedido explícito do usuário.

**Atenção pós-rename (03/08/2026, ver [[projeto_renomeado_relatorios]]):** o repositório foi renomeado de `arecomarcelo/sgr` para `arecomarcelo/relatorios`, e o caminho local de `.../nova-estrutura/sgr` para `.../nova-estrutura/relatorios`. Se esse hook depender de caminho absoluto ou nome de repo antigos (cron/systemd apontando para o caminho/nome antigos), ele pode ter parado de funcionar novamente após este segundo rename — nenhuma referência a esse hook foi localizada no repositório, crontab ou systemd durante a investigação anterior (movimentação de pasta), então sua origem exata segue desconhecida. Se o padrão de auto-commit "Commit N" parar de aparecer, checar isso primeiro.

**Confirmado inativo em 04/08/2026:** durante toda uma sessão inteira (criação do Relatório Comparativo, vários commits necessários — 150→154), o hook não disparou nenhuma vez; todos os commits precisaram ser feitos manualmente (`git add`/`git commit`/`git push`), incluindo a atualização de `Ajustes.md` (que antes era preenchido sozinho pelo hook). Ou seja, a suspeita acima se confirmou: o hook parou de funcionar após o rename SGR → Relatórios. **A partir de agora, tratar como definitivamente manual** — sempre commitar/pushar explicitamente quando o usuário pedir (ou ao seguir o protocolo de Finalizar Sessão), sem esperar o hook agir sozinho. Origem do hook permanece desconhecida (não vale a pena investigar mais sem pedido explícito do usuário).
