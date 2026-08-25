---
name: streamlit-markdown-html-bug
description: "Gotcha real do Relatórios (25/08/2026): linha em branco dentro de HTML passado a st.markdown(unsafe_allow_html=True) quebra a renderização a partir dali"
metadata: 
  node_type: memory
  type: project
  originSessionId: 07a760e9-b389-4cc6-950e-303c1c6d5cb7
  modified: 2026-08-25T14:20:11.334Z
---

Ao gerar HTML customizado (ex.: Cards) para `st.markdown(html, unsafe_allow_html=True)`, **nunca deixar uma linha em branco dentro do bloco HTML** — mesmo só por legibilidade no código-fonte Python (f-string multilinha com `\n\n` entre seções).

**Causa:** o parser Markdown do Streamlit segue CommonMark — um bloco que começa com uma tag HTML de nível de bloco (`<div>`, `<style>`, etc.) é tratado como "HTML bruto" (renderizado direto) **só até a primeira linha em branco**. Depois disso, o parser volta ao modo Markdown normal, onde texto indentado (4+ espaços) vira bloco de código — aparece como texto cru na tela em vez de renderizado.

**Sintoma real observado** ([[projeto_dashboard_campanhas]], 25/08/2026): no Dashboard de Campanhas, o topo do Card (título + badge, antes da primeira linha em branco no f-string) renderizava normalmente; tudo depois (seções Desempenho/Custo/Conversão) aparecia como texto HTML cru.

**Armadilha ao validar:** testar o mesmo HTML direto num navegador (ex.: página HTML estática de pré-visualização) **não reproduz o bug** — só acontece dentro do parser Markdown real do Streamlit. A validação confiável é gerar o HTML e checar programaticamente `"\n\n" not in html`, ou (melhor, mas mais trabalhoso) rodar via `AppTest` e inspecionar `at.markdown[i].value`.

**How to apply:** ao montar HTML multilinha para `st.markdown`, construir por concatenação de strings sem linhas vazias (`"".join([...])` ou strings encadeadas), nunca por f-string triplo-aspas com blocos separados por linha em branco. Vale para qualquer novo Card/painel custom neste projeto ou em outros que usem o mesmo padrão (`comparativo.py::_render_card_destaque` também usa f-string HTML — não tinha linha em branco por sorte, mas vale revisar se for editado).
