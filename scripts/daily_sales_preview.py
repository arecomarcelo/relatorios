"""Render one filtered sales-report panel for screenshot delivery via Slack.

Run inside the reports app container with Streamlit. The page reuses the
production dashboard's own rendering functions; it is not a second chart design.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys

import streamlit as st

sys.path.insert(0, "/app")

from scripts.daily_sales_report_runner import (  # noqa: E402
    filters_for_report_day,
    is_preview_token_valid,
    parse_report_date,
)

sys.path.insert(0, "/app")

_original_set_page_config = st.set_page_config
_original_set_page_config(
    page_title="Relatórios de Vendas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)
if not is_preview_token_valid(
    os.environ.get("DAILY_SALES_PREVIEW_TOKEN"), st.query_params.get("token")
):
    st.error("Acesso não autorizado.")
    st.stop()

st.session_state["keep_alive_started"] = True
st.set_page_config = lambda *args, **kwargs: None

dashboard_spec = importlib.util.spec_from_file_location("sgr_dashboard", "/app/app.py")
if dashboard_spec is None or dashboard_spec.loader is None:
    raise ImportError("Não foi possível carregar o módulo do dashboard de vendas.")
dashboard = importlib.util.module_from_spec(dashboard_spec)
sys.modules[dashboard_spec.name] = dashboard
dashboard_spec.loader.exec_module(dashboard)

st.set_page_config = _original_set_page_config

st.markdown(
    """
    <style>
      header[data-testid="stHeader"],
      div[data-testid="stToolbar"],
      div[data-testid="stDecoration"] { display: none !important; }
      section[data-testid="stSidebar"] { display: none !important; }
      .block-container {
        max-width: 100% !important;
        width: 100% !important;
        padding: 0.25rem !important;
      }
      section.main > div { max-width: 100%; padding-left: 0.25rem; padding-right: 0.25rem; }
      html, body, #root, .stApp,
      div[data-testid="stAppViewContainer"],
      div[data-testid="stMain"], section.main, .block-container {
        height: auto !important;
        max-height: none !important;
        overflow: visible !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

try:
    report_day = parse_report_date(st.query_params.get("date", ""))
except ValueError:
    st.error("Data do relatório ausente ou inválida; use YYYY-MM-DD.")
    st.stop()

report_kind = st.query_params.get("report", "")
if report_kind not in {"metrics", "sellers", "products"}:
    st.error("Tipo de relatório ausente ou inválido.")
    st.stop()

filters = filters_for_report_day(report_day)
st.session_state["data_inicio_filtro"] = filters["data_inicio"]
st.session_state["data_fim_filtro"] = filters["data_fim"]
st.session_state["vendedores_filtro"] = None
st.session_state["situacoes_filtro"] = None
st.session_state["origens_filtro"] = None

try:
    dashboard.apply_theme()
    df_vendas = dashboard.vendas_service.get_vendas_filtradas(
        data_inicio=filters["data_inicio"],
        data_fim=filters["data_fim"],
    )
    if not df_vendas.empty:
        vendas_datas = dashboard.pd.to_datetime(df_vendas["Data"], errors="coerce").dt.date
        if not vendas_datas.eq(report_day).all():
            raise RuntimeError("A consulta retornou vendas fora do período solicitado.")
    metricas = dashboard.vendas_service.get_metricas_vendas(df_vendas)
except Exception:
    st.error("Não foi possível carregar os dados do período solicitado.")
    logging.getLogger(__name__).exception("Falha ao montar painel diário de vendas")
    st.stop()

st.session_state["df_vendas"] = df_vendas
st.session_state["metricas"] = metricas


def render_readiness_marker(report_name: str, card_count: int) -> None:
    """Expose validated period/filter metadata after the report panel is rendered."""
    st.markdown(
        f'<div id="daily-sales-report-ready" data-report="{report_name}" '
        f'data-date="{report_day.isoformat()}" '
        f'data-start="{filters["data_inicio"].isoformat()}" '
        f'data-end="{filters["data_fim"].isoformat()}" '
        'data-applied-filters="data_inicio,data_fim" data-other-filters="none" '
        f'data-sales-count="{len(df_vendas)}" data-card-count="{card_count}" '
        'style="display:none"></div>',
        unsafe_allow_html=True,
    )


if report_kind == "metrics":
    with st.container():
        col_title, col_spacer, col_excel, col_csv = st.columns([3, 1, 1, 1])
        with col_title:
            st.subheader("💎 Métricas de Vendas")
        with col_excel:
            if not df_vendas.empty:
                from io import BytesIO

                buffer_excel = BytesIO()
                with dashboard.pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:
                    df_vendas.to_excel(writer, index=False, sheet_name="Vendas")
                st.download_button(
                    label="📊 Exportar Excel",
                    data=buffer_excel.getvalue(),
                    file_name=f"vendas_filtradas_{report_day:%Y%m%d}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="daily_export_excel",
                )
            else:
                st.button("📊 Exportar Excel", disabled=True, use_container_width=True)
        with col_csv:
            if not df_vendas.empty:
                st.download_button(
                    label="📄 Exportar CSV",
                    data=df_vendas.to_csv(index=False),
                    file_name=f"vendas_filtradas_{report_day:%Y%m%d}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="daily_export_csv",
                )
            else:
                st.button("📄 Exportar CSV", disabled=True, use_container_width=True)
    dashboard._render_metrics_cards(metricas)
    dashboard._render_metrics_produtos()
    render_readiness_marker("metrics", 8)
elif report_kind == "sellers":
    st.subheader("🏆 Ranking de Vendedores")
    vendas_por_vendedor = dashboard.vendas_service.get_vendas_por_vendedor(
        df_vendas, top_n=10
    )
    dashboard._render_vendedores_com_fotos(vendas_por_vendedor)
    render_readiness_marker("sellers", 12)
else:
    st.subheader("🏆 Ranking de Produtos")
    venda_ids = df_vendas["ID_Gestao"].tolist() if not df_vendas.empty else None
    ranking_produtos = dashboard._get_ranking_produtos(
        data_inicio=filters["data_inicio"],
        data_fim=filters["data_fim"],
        vendedores=None,
        situacoes=None,
        venda_ids=venda_ids,
        top_n=10,
    )
    dashboard._render_ranking_produtos(ranking_produtos)
    render_readiness_marker("products", min(len(ranking_produtos), 10))
