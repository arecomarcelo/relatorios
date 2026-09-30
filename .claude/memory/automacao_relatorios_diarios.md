---
name: automacao-relatorios-diarios
description: "Regras funcionais e operacionais da automação diária de relatórios de vendas do SGR legado."
metadata:
  type: project
---

# Automação diária de relatórios

- Este repositório é o SGR legado em Streamlit; não confundir com `relatorios-novo`, a extração Django independente.
- O único filtro aplicado é o intervalo de datas. `data_inicio` e `data_fim` devem ser iguais ao dia anterior da execução em `America/Sao_Paulo`; vendedor, situação, origem e os demais filtros permanecem sem seleção.
- A rotina gera três capturas PNG da interface real, sempre nesta ordem: `metrics`, `sellers`, `products`. O job só deve entregar os arquivos se o JSON de pré-execução validar o estado, período, filtros e exatamente esses três relatórios; não enviar por uma ferramenta alternativa.
- O preview temporário roda em porta aleatória na rede Docker `traefik_public`, mas exige token aleatório por execução antes de importar o dashboard ou consultar dados. O script testa a negação sem token e com token incorreto e remove o proxy ao encerrar; não retirar essa proteção nem publicar o preview sem autenticação.
- Configuração verificada em 29/09/2026: Hermes Cron no perfil `ti`, job `b73d94fc590c`, diariamente às 07:30 (`30 7 * * *`), destino `slack:C0C4T76PJ67`, script `daily_sales_capture.sh`. O slot das 07:00 está reservado ao job separado `Sincronizacao CLIs Hostinger` (`0f028eb5ccc9`).
- Na revisão com autenticação de 29/09/2026, os três PNGs para 28/09 foram gerados, as sondas sem token e com token incorreto foram negadas e os 14 testes do runner passaram; o job de relatórios ainda não tinha execução automática registrada. Não afirmar entrega automática até confirmar uma execução agendada e o recebimento no Slack.

**Realizado em VPS via Hermes VPS**
