---
name: projeto-autocommit
description: "O repositório Relatórios (antigo SGR) tem um hook/processo externo que auto-commita e faz push com mensagens genéricas \"Commit N\" — checar git log antes de tentar commitar manualmente"
metadata:
  node_type: memory
  type: project
  originSessionId: b7e04927-9c7f-4360-8285-1c4e23ff3997
---

Observado em 17/07/2026: alterações feitas em arquivos do projeto (ex.: `apps/vendas/pedidos.py`, `Historico.md`) foram commitadas e enviadas ao `origin/main` automaticamente por um processo externo à sessão do Claude Code — sem que o comando `git commit`/`git push` tivesse sido executado nesta conversa. O commit apareceu com mensagem genérica sequencial ("Commit 148", seguindo commits anteriores "Commit 147", "Commit 146"...) e também atualizou sozinho `documentacao/recursos/Ajustes.md` com uma entrada no formato `##### hh:mm - Commit nnn`.

Isso bate com o padrão descrito no CLAUDE.md global (predeploy/hook que atualiza `Ajustes.md` e faz auto-commit), mas aqui parece disparar por simples alteração de arquivo (save), não só no ciclo de deploy.

**Como aplicar:** antes de rodar `git add`/`git commit`/`git push` manualmente neste projeto, sempre rodar `git status`/`git log --oneline -3` primeiro — é bem possível que o hook já tenha commitado e feito push sozinho, tornando a ação manual redundante (ou gerando confusão se tentar commitar algo que já foi commitado). Não tentar "desfazer" ou alterar esse hook sem pedido explícito do usuário.

**Atenção pós-rename (03/08/2026, ver [[projeto_renomeado_relatorios]]):** o repositório foi renomeado de `arecomarcelo/sgr` para `arecomarcelo/relatorios`, e o caminho local de `.../nova-estrutura/sgr` para `.../nova-estrutura/relatorios`. Se esse hook depender de caminho absoluto ou nome de repo antigos (cron/systemd apontando para o caminho/nome antigos), ele pode ter parado de funcionar novamente após este segundo rename — nenhuma referência a esse hook foi localizada no repositório, crontab ou systemd durante a investigação anterior (movimentação de pasta), então sua origem exata segue desconhecida. Se o padrão de auto-commit "Commit N" parar de aparecer, checar isso primeiro.
