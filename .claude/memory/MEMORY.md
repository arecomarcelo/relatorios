# Memória do Projeto Relatórios (antigo SGR)

- [Projeto renomeado de SGR para Relatórios](projeto_renomeado_relatorios.md) — rename completo (pasta/repo/VPS/branding) em 03/08/2026, organizacional/temporário
- [Projeto movido para nova-estrutura](projeto_movido_nova_estrutura.md) — histórico da movimentação de pasta (03/08/2026) e do rename subsequente
- [Natureza do Projeto](projeto_natureza.md) — sistema legado monolítico, não é da esteira 00-06 SGA; sem % Desenvolvido/Planejamento
- [Arquitetura de Permissões](projeto_permissoes.md) — menu-only, banco `auth_*` compartilhado entre apps, sem re-checagem no router
- [Auto-commit do repositório](projeto_autocommit.md) — hook externo (mensagens "Commit N") confirmado INATIVO desde 04/08/2026; commits agora são manuais
- [Extração para app Django (relatorios-novo)](projeto_extracao_relatorios.md) — estado pós-rename: Relatórios (este repo) é o app publicado em relatorios.oficialsport.com.br; `relatorios-novo` é a extração Django separada, ainda não publicada
- [Divergência do main 05/08/2026](projeto_divergencia_main_20260805.md) — main do GitHub reescrito com a linhagem Streamlit (histórias não relacionadas); trabalho Django antigo preservado em `backup/note-casa-django-20260723`, decisão do usuário de manter main = origin/main
