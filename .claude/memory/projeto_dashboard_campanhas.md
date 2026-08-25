---
name: projeto-dashboard-campanhas
description: "Dashboards de Campanha Adwords (25/08/2026) e Campanha Meta (25/08/2026) — únicos módulos do Relatórios cuja fonte de dados é um arquivo .xlsx (não o Postgres), com upload dinâmico pela própria tela"
metadata:
  node_type: memory
  type: project
  originSessionId: 07a760e9-b389-4cc6-950e-303c1c6d5cb7
  modified: 2026-08-25T18:34:41.144Z
---

Dois módulos irmãos, mesmo padrão de código e layout: `apps/vendas/campanhas.py` (sub-item **"Campanha Adwords"**, permissão `view_campanhas`/`change_campanhas`) e `apps/vendas/campanha_meta.py` (sub-item **"Campanha Meta"**, permissão `view_campanha_meta`/`change_campanha_meta`), ambos no grupo Vendas do menu. `original_name` interno de roteamento: `"Dashboard de Campanhas"` e `"Dashboard de Campanha Meta"` — não mexer nisso. Diferente de todos os outros módulos do Relatórios, **nenhum dos dois lê do Postgres** — leem direto um arquivo `.xlsx` via pandas. Ver [[projeto_permissoes]] para o histórico de permissões granulares do projeto.

**Formato do arquivo de origem (comum aos dois):** aba única, cabeçalho real na linha 3 (`header=2` no `pd.read_excel`), últimas linhas são total/rodapé sem valor no nome da campanha (descartadas via `dropna`).
- **Adwords:** linha 2 traz o período em texto livre (ex.: "1 de agosto de 2026 - 25 de agosto de 2026"). Colunas com fração (CTR, % de impr., Taxa de conv.) precisam ser multiplicadas por 100 ao formatar/plotar.
- **Meta:** não tem linha de período — é derivado das colunas por linha "Início dos relatórios"/"Encerramento dos relatórios" (mín/máx do arquivo inteiro). **CTR (e afins) já vem em pontos percentuais** (ex.: `1.148703` = 1,15%) — **não multiplicar por 100** aqui (diferença crítica em relação ao Adwords, achado real ao implementar). Campanhas sem "Tipo de resultado"/"Resultados" configurados (posts sem métrica) tratadas com fallback "N/A".

**Resolução do caminho do arquivo (3 níveis, resolvidos a cada leitura via `_resolver_caminho_xlsx()`, nunca uma constante fixa) — mesmo padrão nos dois módulos:**
1. Variável de ambiente override (`CAMPANHAS_XLSX_PATH` / `CAMPANHA_META_XLSX_PATH` no `.env`) — raro.
2. Arquivo "vivo" em `data/` (`Relatorio Adwords.xlsx` / `Relatorio Meta.xlsx`) — **volume gravável**, montado em produção via `stack.yml` (`/home/deploy/apps/relatorios/data:/app/data`, compartilhado pelos dois módulos, sem precisar de novo volume para o Meta). É onde o botão de upload da tela grava. `/data/` está no `.gitignore` — nunca versionado.
3. Arquivo **semente** versionado no git (`documentacao/Relatorio Adwords.xlsx` / `documentacao/Relatório Meta.xlsx`), acompanha a imagem Docker. Usado só até o primeiro upload acontecer (bootstrap).

**Atualização dinâmica (upload pela tela):** seção "📤 Atualizar Arquivo de Origem" no próprio Dashboard, visível só para `admin` (bypass) ou quem tiver a permissão `change_*` (banco, mesmo `ContentType` id 213 das demais permissões granulares — nasce sem ninguém atribuído: Adwords id 745/746, Meta id 747/748). Valida colunas do arquivo enviado antes de substituir, grava atomicamente (`tempfile` + `os.replace`) em `data/`. **Gotcha de permissão:** `change_*` sozinha não adianta sem `view_*` também — sem essa, o usuário nem chega na tela para ver o botão.

**Layout (Cards, 3 por linha, métricas agrupadas em seções, badge de tipo, barra de destaque no topo, título centralizado):**
- **Adwords:** seções Desempenho (Cliques/Impressões/CTR), Custo (CPC Médio/Custo/Custo por Conv.), caixa "% Impressão" (1ª posição/parte superior), Conversão (Conversões/Taxa de Conversão).
- **Meta:** seções Desempenho (Impressões/Alcance/Cliques no Link/CTR — grid de 4), Custo (CPC/CPM/Valor Gasto), caixa "Resultado" (Resultados/Custo por Resultado) — substitui a caixa "% Impressão", que não existe no export do Meta.
- Seção **"📊 Comparativo entre Campanhas"** (expander, expandido por padrão) com 6 gráficos de barras horizontais (Plotly, `color_continuous_scale="Blues"`) em cada módulo — Adwords: Impressões, Cliques, CTR, Taxa de Conversão, Custo, CPC Médio; Meta: Impressões, Cliques no Link, CTR, Resultados, Valor Gasto, CPC. Ordenados por valor (maior no topo), rótulo formatado direto na barra, eixo X oculto, nomes de campanha truncados no eixo Y com nome completo no hover.
- Expander "🔄 Informações de Atualização" (mesmo padrão visual do Relatório de Vendas/Comparativo) mostra Data/Hora da última modificação do **arquivo ativo** (não do banco) + Período.

**Gotcha real já corrigido — linha em branco quebra `st.markdown(unsafe_allow_html=True)`:** ver [[streamlit-markdown-html-bug]] — vale para qualquer HTML custom nesses módulos (Cards). Validado com teste automatizado (`assert '\n\n' not in html`) ao criar o módulo Meta.

**Why:** únicos pontos do sistema com fonte de dados fora do Postgres — relevante para qualquer skill/auditoria futura que assuma "todo módulo lê do banco `sga`".

**How to apply:** ao dar manutenção nesses módulos, não tentar usar `VendasService`/`DIContainer` — é `pandas.read_excel` direto, sem camada repository/service. Ao editar o HTML dos Cards ou adicionar novo `st.markdown(html, unsafe_allow_html=True)`, nunca deixar linha em branco no meio do HTML. Ao criar um terceiro dashboard do mesmo tipo (nova plataforma de ads), copiar `campanha_meta.py` como base e **conferir a escala das colunas percentuais no arquivo real antes de formatar/plotar** — cada exportador de ads tem sua própria convenção (fração vs. pontos percentuais).
