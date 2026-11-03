---
name: ranking-vendedores-cadastro
description: Ranking de Vendedores lê vendas."Vendedores" (ExibirRanking + Foto do banco) desde 03/11/2026; lista fixa de 12 nomes e fotos/ aposentadas
metadata:
  type: project
---

Desde 03/11/2026 (commit `9cd623b9`, em produção) `_render_vendedores_com_fotos` (`app.py`) lê `VendaRepository.get_vendedores_ranking()`: só vendedores com `ExibirRanking`, com a foto PNG gravada no banco pela app vendas. A lista fixa de 12 nomes e as fotos `fotos/N.png` saíram do código; a pasta `fotos/` ficou só como backup (pode ser apagada quando o usuário quiser).

- Cálculos (vendas do período, ano anterior, meta) iguais aos de antes — ocultar só tira o card (regra explícita do usuário).
- Cards em linhas de 6, sem teto de 12; a função devolve a quantidade de cards, usada no marcador `data-card-count` da automação diária (`scripts/daily_sales_preview.py`, antes 12 fixo).
- O app.py se testa carregando pelo caminho (`importlib`), porque `app` é o pacote Django — ver `tests/test_ranking_vendedores.py`.
- Edição pela tela Vendedores da app vendas (dona da tabela). Ver [[automacao-relatorios-diarios]].

**Why:** o usuário quis ocultar vendedores do Ranking pelo cadastro, sem mexer em cálculo.
**How to apply:** mudanças de colunas em `vendas."Vendedores"` exigem deploy da vendas antes do relatorios; não reintroduzir lista fixa de vendedores.

Realizado em Note_Oficial via Claude Code.
