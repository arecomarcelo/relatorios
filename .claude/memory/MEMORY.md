# Memória do Projeto Relatórios (antigo SGR)

- ✅ [Porta 8112 exposta na internet, corrigida](porta-8112-exposta-corrigida-17-08.md) — bug do Docker Swarm ingress, mitigado via iptables DROP (17/08/2026)
- [Projeto renomeado de SGR para Relatórios](projeto_renomeado_relatorios.md) — rename completo (pasta/repo/VPS/branding) em 03/08/2026, organizacional/temporário
- [Projeto movido para nova-estrutura](projeto_movido_nova_estrutura.md) — histórico da movimentação de pasta (03/08/2026) e do rename subsequente
- [Natureza do Projeto](projeto_natureza.md) — legado Streamlit do ecossistema oficial; exceção histórica ao Planejamento foi supersedida pelo protocolo global atual
- [Arquitetura de Permissões](projeto_permissoes.md) — menu-only, banco `auth_*` compartilhado entre apps, sem re-checagem no router
- [Auto-commit do repositório](projeto_autocommit.md) — hook externo (mensagens "Commit N") confirmado INATIVO desde 04/08/2026; commits agora são manuais
- [Extração para app Django (relatorios-novo)](projeto_extracao_relatorios.md) — estado pós-rename: Relatórios (este repo) é o app publicado em relatorios.oficialsport.com.br; `relatorios-novo` é a extração Django separada, ainda não publicada
- [Incidente: rotação de senha do legado quebrou a app (ago/2026)](rotacao_senha_legado_ago2026.md) — 05/08/2026, app fora do padrão Django não foi pega na varredura inicial; corrigida, mas atenção em próximas rotações; `.env` local da Note_Oficial também estava desatualizado (corrigido 25/08/2026)
- [Dashboards de Campanha Adwords e Campanha Meta](projeto_dashboard_campanhas.md) — 25/08/2026, únicos módulos com fonte de dados em arquivo .xlsx (não Postgres); Cards + gráficos comparativos + upload dinâmico (permissões `view_campanhas`/`change_campanhas` e `view_campanha_meta`/`change_campanha_meta`); CTR do Meta já vem em pontos percentuais, diferente do Adwords (fração)
- [Bug: linha em branco quebra HTML no st.markdown](streamlit_markdown_html_bug.md) — 25/08/2026, CommonMark encerra bloco HTML bruto na primeira linha vazia; preview em navegador puro não reproduz
- [Bug: UnicodeEncodeError no logging em produção](logging_encoding_bug.md) — 25/08/2026, sys.stderr reportava ascii em threads do Streamlit mesmo com PYTHONIOENCODING=utf-8; corrigido com reconfigure() em core/logging_config.py
- [scripts/deploy_local.sh sempre retorna exit 1 fora de terminal interativo](deploy_local_falso_exit1.md) — 25/08/2026, ssh consome o stdin do read -p final; não confiar só no exit code ao rodar via CLI/agente, confirmar com curl + logs
- [Automação diária de relatórios](automacao_relatorios_diarios.md) — regras da geração incremental: só data do dia anterior, três capturas PNG e cron das 07:30 (configuração verificada em 29/09/2026)
