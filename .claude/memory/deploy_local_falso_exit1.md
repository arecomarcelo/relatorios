---
name: deploy-local-falso-exit1
description: "scripts/deploy_local.sh sempre retorna exit code 1 quando executado com stdin não-interativo (ex.: via Claude Code Bash), mesmo com deploy 100% bem-sucedido — não é falha real"
metadata:
  node_type: memory
  type: project
  originSessionId: cec14d61-c34f-4540-aef6-154ee5849b63
  modified: 2026-08-25T19:27:35.690Z
---

`scripts/deploy_local.sh` termina com `read -p "Pressione ENTER para fechar..."` (só faz sentido em terminal interativo). Ao rodar o script de forma não-interativa (ex.: `echo | bash scripts/deploy_local.sh`, como o Claude Code precisa fazer para não travar o Bash tool esperando ENTER), o `ssh` usado na etapa "[3/4] Conectando à VPS" **consome o stdin por padrão** (não tem a flag `-n`) — a linha vazia enviada para satisfazer o `read` final acaba sendo engolida pelo `ssh`, e o `read` fica sem entrada nenhuma. Isso faz o script inteiro terminar com **exit code 1**, mesmo quando todas as etapas reais (push, build, push da imagem, `git pull` + `docker stack deploy` na VPS, verificação de réplicas) tiveram sucesso e o log mostra "✅ DEPLOY CONCLUÍDO!".

Confirmado real em duas execuções na sessão de 25/08/2026 (deploy do Dashboard de Campanha Meta e deploy da correção de encoding do logging) — as duas vezes o script "falhou" (exit 1) com o deploy 100% funcional.

**Why:** sem essa memória, cada deploy rodado por um CLI/agente (não um humano no terminal) vai gerar um alerta de "falhou" que precisa ser investigado do zero toda vez.

**How to apply:** ao rodar `scripts/deploy_local.sh` de forma não-interativa, **nunca confiar só no exit code** — ler o log completo em busca de "✅ DEPLOY CONCLUÍDO!" e das mensagens de sucesso de cada etapa, e confirmar de forma independente com `curl` no `APP_URL` (`https://relatorios.oficialsport.com.br`) + `docker service ps`/`docker logs` na VPS antes de reportar sucesso ou falha ao usuário. Correção definitiva ficaria em adicionar `-n` ao comando `ssh` do script e/ou remover o `read -p` final (ou trocar por algo condicional a terminal interativo, ex.: `[ -t 0 ] && read -p ...`) — não aplicada ainda, pendente se o usuário quiser tornar o script mais robusto para execução por CLI/agente.
