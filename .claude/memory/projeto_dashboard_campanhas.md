---
name: projeto-dashboard-campanhas
description: "Dashboard de Campanhas Adwords (25/08/2026) — único módulo do Relatórios cuja fonte de dados é um arquivo .xlsx (não o Postgres), com upload dinâmico pela própria tela"
metadata: 
  node_type: memory
  type: project
  originSessionId: 07a760e9-b389-4cc6-950e-303c1c6d5cb7
  modified: 2026-08-25T17:03:51.788Z
---

`apps/vendas/campanhas.py` — sub-item **"Campanha Adwords"** do grupo Vendas no menu (rótulo renomeado de "Campanhas" em 25/08/2026; `original_name` interno de roteamento continua `"Dashboard de Campanhas"`, não mexer nisso). Permissão de visualização: `view_campanhas`. Diferente de todos os outros módulos do Relatórios, **não lê do Postgres** — lê direto um arquivo `.xlsx` (export de Performance de Campanhas do Google Ads) via pandas. Ver [[projeto_permissoes]] para o histórico de permissões granulares do projeto.

**Formato do arquivo de origem:** aba única, cabeçalho real na linha 3 (`header=2` no `pd.read_excel`), linha 2 traz o período do relatório em texto livre (ex.: "1 de agosto de 2026 - 25 de agosto de 2026"), últimas linhas são total/rodapé sem valor em "Campanha" (descartadas via `dropna(subset=["Campanha"])`). Colunas com fração (CTR, % de impr., Taxa de conv.) precisam ser multiplicadas por 100 ao formatar como percentual ou ao plotar (senão a barra do gráfico fica desproporcional).

**Resolução do caminho do arquivo (estado atual, pós-25/08/2026) — 3 níveis, resolvidos a cada leitura via `_resolver_caminho_xlsx()`, nunca uma constante fixa:**
1. `CAMPANHAS_XLSX_PATH` (`.env`) — override manual, raro.
2. `data/Relatorio Adwords.xlsx` — **volume gravável**, montado em produção via `stack.yml` (`/home/deploy/apps/relatorios/data:/app/data`, criado com `chmod 777` na VPS antes do 1º deploy com volume). É onde o botão de upload da tela grava. `/data/` está no `.gitignore` — nunca versionado.
3. `documentacao/Relatorio Adwords.xlsx` — arquivo **semente**, versionado no git, acompanha a imagem Docker. Usado só até o primeiro upload acontecer (bootstrap).

**Atualização dinâmica (upload pela tela, implementado 25/08/2026):** seção "📤 Atualizar Arquivo de Origem" no próprio Dashboard, visível só para `admin` (bypass) ou quem tiver a permissão **`change_campanhas`** (banco, id 746, mesmo `ContentType` id 213 das demais permissões granulares — nasce sem ninguém atribuído). Valida colunas do arquivo enviado antes de substituir (não deixa quebrar o dashboard), grava atomicamente (`tempfile` + `os.replace`) em `data/`. **Gotcha de permissão:** `change_campanhas` sozinha não adianta sem `view_campanhas` também — sem essa, o usuário nem chega na tela para ver o botão.

**Layout (evoluiu bastante ao longo do dia 25/08/2026):**
- Campanha é um **Card** (não mais painel/expander) — grid de 3 por linha, métricas agrupadas em seções (Desempenho/Custo/% Impressão/Conversão), badge de Tipo de campanha, barra de destaque no topo, título centralizado.
- Seção **"📊 Comparativo entre Campanhas"** (expander, expandido por padrão) com 6 gráficos de barras horizontais (Plotly, `color_continuous_scale="Blues"` — mesmo padrão do resto do app): Impressões, Cliques, CTR, Taxa de Conversão, Custo, CPC Médio. Ordenados por valor (maior no topo), rótulo formatado direto na barra, eixo X oculto, nomes de campanha truncados no eixo Y com nome completo no hover. "Alcance" foi pedido mas **não existe** no arquivo de origem — removido da lista a pedido do usuário.
- Expander "🔄 Informações de Atualização" (mesmo padrão visual do Relatório de Vendas/Comparativo) mostra Data/Hora da última modificação do **arquivo ativo** (não do banco) + Período lido do cabeçalho da planilha.

**Gotcha real já corrigido — linha em branco quebra `st.markdown(unsafe_allow_html=True)`:** ver [[streamlit-markdown-html-bug]] — vale para qualquer HTML custom neste módulo (Cards).

**Pendência em aberto (26/08 em diante, se for retomado):** apareceu um arquivo novo `documentacao/Relatório Meta.xlsx` na pasta (~13:32 de 25/08/2026), fora do que foi pedido nesta sessão — não commitado, perguntado ao usuário se é para um futuro Dashboard de Meta Ads (resposta ainda não recebida até o fim desta sessão).

**Why:** único ponto do sistema com fonte de dados fora do Postgres — relevante para qualquer skill/auditoria futura que assuma "todo módulo lê do banco `sga`".

**How to apply:** ao dar manutenção neste módulo, não tentar usar `VendasService`/`DIContainer` — é `pandas.read_excel` direto, sem camada repository/service. Ao editar o HTML dos Cards ou adicionar novo `st.markdown(html, unsafe_allow_html=True)`, nunca deixar linha em branco no meio do HTML.
