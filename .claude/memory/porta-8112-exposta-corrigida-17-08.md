---
name: porta-8112-exposta-corrigida-17-08
description: "RESOLVIDO (17/08/2026): porta 8112 estava sem proteção de firewall (bug do Docker Swarm ingress) — corrigida via iptables DROP"
metadata:
  type: project
---

Em 17/08/2026 (sessão no projeto Cadastros, Note_Oficial, Claude Code), verificação de
portas em produção encontrou que `relatorios` (porta **8112**) não tinha a regra de
firewall que protege a maioria das apps irmãs contra a exposição real da porta na
internet.

**Causa:** `ports: "127.0.0.1:8112:8112"` no `stack.yml` é **ignorado pelo modo
`ingress` do Docker Swarm** (limitação conhecida) — a porta é publicada de verdade em
`0.0.0.0`. A mitigação real é uma regra `iptables DROP` na chain `DOCKER-USER`, que só
existia para 6/12 apps — `relatorios` não estava entre elas (não testado
individualmente da internet nesta sessão, mas no mesmo padrão de `comex`/`cadastros`,
confirmados expostos).

**Correção aplicada (na VPS, fora deste repositório):**
`iptables -A DOCKER-USER -i eth0 -p tcp --dport 8112 -j DROP`, persistida com
`netfilter-persistent save`.

**Why:** exposição real de aplicação Django direto na internet, sem passar pelo
domínio/SSL/proxy.

**How to apply:** nenhuma ação necessária no código deste repositório — correção só de
infraestrutura (firewall da VPS). Se a stack for recriada do zero num node novo,
confirmar `iptables -L DOCKER-USER -n | grep 8112`.
