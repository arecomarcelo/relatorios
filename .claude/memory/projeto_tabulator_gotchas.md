---
name: projeto-tabulator-gotchas
description: Três gotchas reais do Tabulator.js descobertos na Fase 1 (Estoque) que afetam toda grid futura (Fases 2-5)
metadata: 
  node_type: memory
  type: project
  originSessionId: b767fed9-fc23-4775-add8-98b0eaaedb85
  modified: 2026-07-23T00:14:14.392Z
---

Três problemas reais encontrados ao implementar a grid de Estoque (Fase 1, 22/07/2026), que valem
para qualquer grid Tabulator futura do projeto (Recebimentos, Comex, Pedidos, SAC — Fases 2-5).
Ver [[projeto_scaffolding]] e [[projeto_planejamento]].

**1. Bug de contraste (texto branco sobre fundo branco):**
O tema padrão do Tabulator define `.tabulator .tabulator-tableholder .tabulator-table {
background-color:#fff }` — um seletor de 3 classes. O primeiro override em
`static/css/tabulator-dark.css` usava só `.tabulator .tabulator-table` (2 classes), especificidade
menor, então o branco padrão vencia e os dados ficavam invisíveis (texto branco var(--os-text)
sobre fundo branco). Corrigido igualando a especificidade exata do seletor. Verifique sempre a
especificidade real do seletor do tema Tabulator (via CSSOM, não só assumir) ao sobrescrever
qualquer regra do tema padrão — colar 2 classes pode não ser suficiente.

**Why:** especificidade CSS é (IDs, classes, elementos) comparada em ordem; um seletor com mais
classes sempre vence independente da ordem de carregamento do stylesheet.

**How to apply:** ao criar CSS para novas grids (Fases 2-5), sempre inspecionar via
`document.styleSheets`/`getComputedStyle` se o seletor de override realmente vence, em vez de só
confiar na leitura do arquivo CSS.

**2. Filtro em lista multi-seleção precisa de `headerFilterFunc:"in"` explícito:**
`headerFilter:"list"` com `headerFilterParams:{valuesLookup:true, multiselect:true}` sozinho NÃO
funciona — o Tabulator compara a string concatenada das seleções contra o valor da célula por
igualdade exata, retornando zero resultados sempre que mais de um valor é marcado. É obrigatório
adicionar `headerFilterFunc:"in"` na definição da coluna para o matching funcionar como
"valor está contido na lista selecionada".

**Why:** confirmado testando no navegador (mockup HTML standalone com Tabulator real) — sem
`headerFilterFunc:"in"`, selecionar "GALPÃO 01"+"GALPÃO 02" retornava "Nenhum produto encontrado"
mesmo havendo linhas correspondentes.

**How to apply:** usar esse padrão (`headerFilter:"list"` + `headerFilterParams` com
`valuesLookup:true, multiselect:true, clearable:true` + `headerFilterFunc:"in"`) em toda coluna de
texto categórica das próximas grids (Fases 2-5), replicando o "Set Filter" do legado AgGrid
(confirmado visualmente rodando o SGR legado localmente — colunas de texto têm filtro em lista com
checkbox+busca; colunas numéricas usam filtro simples "Igual a", sem lista).

**Meta-lição:** a análise estática do código do legado (grep por `agSetColumnFilter`,
`streamlit-aggrid` sem Enterprise) indicou que esse filtro em lista NÃO deveria existir — mas o
teste visual real (rodando o legado localmente e clicando no funil) mostrou que existe. Para
paridade de UI/UX, sempre validar rodando a tela real, não só ler o código.

**3. `valuesLookup:true` não faz cascata entre colunas (lista mostra valores de TODA a tabela):**
Reportado pelo usuário em 22/07/2026: filtrando Grupo="CARDIO" (grid mostra só 1 produto), o
dropdown do filtro de Nome continuava listando os nomes de TODOS os 1707 produtos, não só o do
grupo filtrado. Causa: `valuesLookup:true` sempre computa a lista a partir do dataset completo,
ignorando os outros filtros já aplicados. Corrigido trocando para `valuesLookup:"active"`, que
computa a lista só a partir das linhas atualmente ativas (respeitando os demais filtros).

**Why:** confirmado no mockup — com Grupo=CARDIO aplicado e `valuesLookup:"active"`, o dropdown de
Nome passou a mostrar só "AIR BIKE" (a única linha visível), replicando o comportamento em cascata
esperado de um Set Filter real.

**Efeito colateral aceitável:** com `"active"`, reabrir o filtro da PRÓPRIA coluna já filtrada
mostra só o valor já selecionado (não a lista completa de opções) — para trocar de valor é preciso
limpar o filtro primeiro (botão "x", já habilitado via `clearable:true`). Tabulator não tem opção
nativa para excluir a própria coluna do cálculo de `"active"`; foi aceito como trade-off razoável
já que o "x" resolve.

**How to apply:** usar sempre `valuesLookup:"active"` (nunca `true`) em `FILTRO_LISTA` de toda
grid Tabulator futura (Fases 2-5) que tiver mais de uma coluna com filtro em lista.
