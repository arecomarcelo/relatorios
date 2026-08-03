"""
SGR - Módulo Vendas - Relatório de Pedidos
Exibe pedidos de vendas com filtros de data, prazo de entrega, situação e vendedor
"""

import io
import logging
import traceback
from datetime import date, datetime

import pandas as pd
import streamlit as st

# Imports da aplicação
try:
    from core.container_vendas import DIContainer
    from core.exceptions import BusinessLogicError, SGRException, ValidationError
    from presentation.styles.theme_simple import apply_theme
except ImportError as e:
    st.error(f"❌ Erro crítico de importação: {e}")
    st.stop()


class PedidosController:
    """Controller para exibição do relatório de pedidos de vendas"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.container = None
        self._initialize_services()

    def _initialize_services(self):
        """Inicializa serviços com tratamento de erro"""
        try:
            self.container = DIContainer()
            self.container.get_vendas_service()
            self.logger.info("Serviços de vendas (Pedidos) inicializados com sucesso")
        except Exception as e:
            self.logger.error(f"Erro na inicialização: {str(e)}")
            st.error(f"❌ Erro na inicialização: {str(e)}")
            st.stop()

    def render_dashboard(self):
        """Renderiza o dashboard do relatório de pedidos"""
        try:
            apply_theme()

            st.markdown(
                "<h1 style='text-align: center; color: #1E88E5;'>📋 Vendas - Relatório de Pedidos</h1>",
                unsafe_allow_html=True,
            )
            st.markdown("---")

            if not self._health_check_silent():
                st.error("❌ Erro ao conectar com o banco de dados")
                return

            # Inicializar estado da sessão
            if "pedidos_df" not in st.session_state:
                st.session_state.pedidos_df = None
                st.session_state.pedidos_load_count = 0
                self._auto_load_current_month()

            self._render_filters_and_data()

        except Exception as e:
            self.logger.error(f"Erro no dashboard: {str(e)}")
            self.logger.error(traceback.format_exc())
            st.error("❌ Erro inesperado no dashboard. Verifique os logs.")
            with st.expander(
                "🔍 Detalhes do erro (clique para expandir)", expanded=True
            ):
                st.code(traceback.format_exc())
                st.error(f"Tipo de erro: {type(e).__name__}")
                st.error(f"Mensagem: {str(e)}")

    def _health_check_silent(self) -> bool:
        """Verifica saúde do sistema silenciosamente"""
        try:
            health = self.container.health_check()
            return all(health.values())
        except Exception as e:
            self.logger.error(f"Erro no health check: {str(e)}")
            return False

    def _auto_load_current_month(self):
        """Carrega dados do mês atual automaticamente na inicialização"""
        try:
            hoje = date.today()
            primeiro_dia = hoje.replace(day=1)
            self.logger.info(
                f"Carregamento automático Pedidos: {primeiro_dia} a {hoje}"
            )
            self._load_pedidos_data(
                data_inicio=primeiro_dia,
                data_fim=hoje,
                prazo_inicio=None,
                prazo_fim=None,
                situacao=None,
                vendedor=None,
                auto=True,
            )
        except Exception as e:
            self.logger.error(f"Erro no carregamento automático: {str(e)}")

    def _get_situacoes(self):
        """Obtém lista de situações disponíveis na tabela Vendas"""
        try:
            from django.db import connection

            query = (
                'SELECT DISTINCT "SituacaoNome" FROM "Vendas" '
                'WHERE "SituacaoNome" IS NOT NULL AND "SituacaoNome" != \'\' '
                'ORDER BY "SituacaoNome"'
            )
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
            return [row[0] for row in rows]
        except Exception as e:
            self.logger.error(f"Erro ao buscar situações: {str(e)}")
            return []

    def _get_vendedores(self):
        """Obtém lista de vendedores ativos"""
        try:
            from django.db import connection

            query = 'SELECT DISTINCT "Nome" FROM "Vendedores" ORDER BY "Nome"'
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
            return [row[0] for row in rows]
        except Exception as e:
            self.logger.error(f"Erro ao buscar vendedores: {str(e)}")
            return []

    def _render_filters_and_data(self):
        """Renderiza seção de filtros e tabela de dados"""
        st.subheader("🔍 Filtros")

        # expanded=True fixo — não usar lógica dinâmica aqui.
        # No Streamlit, expanded=X programático sobrescreve a interação do usuário
        # a cada rerun, impedindo que o botão interno seja processado corretamente.
        with st.expander("Configurar Filtros", expanded=True):
            self._render_filters()

        df = st.session_state.get("pedidos_df")
        if df is not None and not df.empty:
            self._render_data_table()
        elif df is not None and df.empty:
            st.warning("⚠️ Nenhum pedido encontrado para os filtros selecionados.")
        else:
            st.info(
                "ℹ️ **Aguardando busca.**\n\n"
                "Configure os filtros acima e clique em **🔍 Buscar Pedidos**."
            )

    def _render_filters(self):
        """Renderiza os controles de filtro"""
        # Flag para controlar st.rerun() FORA do try/except.
        # st.rerun() lança RerunException (subclasse de Exception).
        # Se chamado dentro de except Exception, a exception é capturada e o rerun não ocorre.
        _should_rerun = False
        try:
            # Linha 1 — Datas do pedido
            col1, col2 = st.columns(2)
            with col1:
                data_inicio = st.date_input(
                    "📅 Data Inicial",
                    value=date.today().replace(day=1),
                    format="DD/MM/YYYY",
                    help="Data inicial do pedido",
                    key="pedidos_data_inicio",
                )
            with col2:
                data_fim = st.date_input(
                    "📅 Data Final",
                    value=date.today(),
                    format="DD/MM/YYYY",
                    help="Data final do pedido",
                    key="pedidos_data_fim",
                )

            # Linha 2 — Prazo de Entrega
            col3, col4 = st.columns(2)
            with col3:
                prazo_inicio = st.date_input(
                    "🚚 Prazo Entrega Inicial",
                    value=None,
                    format="DD/MM/YYYY",
                    help="Data inicial do prazo de entrega (opcional)",
                    key="pedidos_prazo_inicio",
                )
            with col4:
                prazo_fim = st.date_input(
                    "🚚 Prazo Entrega Final",
                    value=None,
                    format="DD/MM/YYYY",
                    help="Data final do prazo de entrega (opcional)",
                    key="pedidos_prazo_fim",
                )

            # Linha 3 — Situação e Vendedor
            situacoes = self._get_situacoes()
            vendedores = self._get_vendedores()

            col5, col6 = st.columns(2)
            with col5:
                situacao_sel = st.selectbox(
                    "📌 Situação",
                    options=["Todas"] + situacoes,
                    index=0,
                    help="Filtrar por situação do pedido",
                    key="pedidos_situacao",
                )
                situacao_val = None if situacao_sel == "Todas" else situacao_sel
            with col6:
                vendedor_sel = st.selectbox(
                    "👤 Vendedor",
                    options=["Todos"] + vendedores,
                    index=0,
                    help="Filtrar por vendedor",
                    key="pedidos_vendedor",
                )
                vendedor_val = None if vendedor_sel == "Todos" else vendedor_sel

            # Linha 4 — Condição de Pagamento
            condicao_map = {"À Vista": "a_vista", "Parcelado": "parcelado"}
            col7, _ = st.columns(2)
            with col7:
                condicao_sel = st.selectbox(
                    "💳 Condição de Pagamento",
                    options=["Todas"] + list(condicao_map.keys()),
                    index=0,
                    help="Filtrar por condição de pagamento",
                    key="pedidos_condicao_pagamento",
                )
                condicao_val = condicao_map.get(condicao_sel)

            # Botões de ação
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
            with col_btn1:
                if st.button(
                    "🔍 Buscar Pedidos",
                    key="btn_buscar_pedidos",
                    type="primary",
                    use_container_width=True,
                    help="Aplicar filtros e buscar pedidos",
                ):
                    self._load_pedidos_data(
                        data_inicio=data_inicio,
                        data_fim=data_fim,
                        prazo_inicio=prazo_inicio,
                        prazo_fim=prazo_fim,
                        situacao=situacao_val,
                        vendedor=vendedor_val,
                        condicao_pagamento=condicao_val,
                        auto=False,
                    )
                    _should_rerun = True
            with col_btn2:
                if st.button(
                    "📅 Mês Atual",
                    key="btn_mes_atual_pedidos",
                    use_container_width=True,
                    help="Carregar pedidos do mês atual",
                ):
                    hoje = date.today()
                    primeiro_dia = hoje.replace(day=1)
                    self._load_pedidos_data(
                        data_inicio=primeiro_dia,
                        data_fim=hoje,
                        prazo_inicio=None,
                        prazo_fim=None,
                        situacao=None,
                        vendedor=None,
                        condicao_pagamento=None,
                        auto=False,
                    )
                    _should_rerun = True

        except Exception as e:
            st.error(f"❌ Erro nos filtros: {str(e)}")

        # FORA do try/except — garante que RerunException não seja capturada
        if _should_rerun:
            st.rerun()

    def _load_pedidos_data(
        self,
        data_inicio: date,
        data_fim: date,
        prazo_inicio,
        prazo_fim,
        situacao,
        vendedor,
        condicao_pagamento=None,
        auto: bool = False,
    ):
        """Carrega pedidos do banco de dados com os filtros informados.

        Nota: NÃO chama st.rerun() — o clique no botão já dispara o rerun
        automaticamente no Streamlit. Chamar st.rerun() aqui levanta
        RerunException que seria capturada pelo except externo, impedindo
        a atualização da tela.
        """
        try:
            from django.db import connection

            query = """
                SELECT
                    "Codigo",
                    "ClienteNome",
                    "VendedorNome",
                    "Data",
                    "PrazoEntrega",
                    "SituacaoNome",
                    "ValorTotal"
                FROM "Vendas"
                WHERE "Data"::DATE BETWEEN %s AND %s
                AND TRIM("VendedorNome") IN (SELECT "Nome" FROM "Vendedores")
            """
            params = [data_inicio, data_fim]

            # Filtro de Prazo de Entrega
            # NULLIF trata strings vazias ("") como NULL, evitando erro de cast
            if prazo_inicio:
                query += " AND NULLIF(TRIM(\"PrazoEntrega\"), '')::DATE >= %s"
                params.append(prazo_inicio)
            if prazo_fim:
                query += " AND NULLIF(TRIM(\"PrazoEntrega\"), '')::DATE <= %s"
                params.append(prazo_fim)

            # Filtro de Situação
            if situacao:
                query += ' AND "SituacaoNome" = %s'
                params.append(situacao)

            # Filtro de Vendedor
            if vendedor:
                query += ' AND "VendedorNome" = %s'
                params.append(vendedor)

            # Filtro de Condição de Pagamento
            if condicao_pagamento:
                query += ' AND "CondicaoPagamento" = %s'
                params.append(condicao_pagamento)

            query += ' ORDER BY "Data" DESC, "Codigo" ASC'

            with connection.cursor() as cursor:
                cursor.execute(query, params)
                columns = [col[0] for col in cursor.description]
                data = cursor.fetchall()

            df = pd.DataFrame(data, columns=columns)

            if df.empty:
                st.session_state.pedidos_df = pd.DataFrame()
                if not auto:
                    st.warning(
                        "⚠️ Nenhum pedido encontrado para os filtros selecionados."
                    )
                return

            # Formatar datas para DD/MM/YYYY
            for col_data in ["Data", "PrazoEntrega"]:
                if col_data in df.columns:
                    df[col_data] = pd.to_datetime(
                        df[col_data], errors="coerce"
                    ).dt.strftime("%d/%m/%Y")
                    df[col_data] = df[col_data].fillna("")

            # Garantir ValorTotal como float
            if "ValorTotal" in df.columns:
                df["ValorTotal"] = pd.to_numeric(
                    df["ValorTotal"], errors="coerce"
                ).fillna(0.0)

            st.session_state.pedidos_df = df
            # Incrementa contador para forçar recriação do AgGrid com nova key
            st.session_state.pedidos_load_count = (
                st.session_state.get("pedidos_load_count", 0) + 1
            )

            if not auto:
                self.logger.info(f"✓ {len(df)} pedidos carregados pelo usuário")
            else:
                self.logger.info(f"✓ {len(df)} pedidos carregados automaticamente")

        except Exception as e:
            st.error(f"❌ Erro ao carregar pedidos: {str(e)}")
            self.logger.error(f"Erro ao carregar pedidos: {str(e)}")
            self.logger.error(traceback.format_exc())

    def _format_br(self, valor: float, decimals: int = 2) -> str:
        """Formata número no padrão brasileiro (ponto como milhar, vírgula como decimal)"""
        if decimals == 0:
            return f"{valor:,.0f}".replace(",", ".")
        formatted = f"{valor:,.{decimals}f}"
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

    def _generate_excel(self, df: pd.DataFrame) -> bytes:
        """Gera Excel formatado no mesmo padrão visual do PDF:
        - Título e data de geração no topo
        - Cabeçalho azul (#1E88E5), texto branco, bold
        - Linhas alternadas branco / cinza claro (#F5F5F5)
        - Linha de total azul claro (#E3F2FD), bold
        - ValorTotal alinhado à direita, formato moeda
        - Datas centralizadas
        - Grade com bordas cinzas
        """
        buffer = io.BytesIO()
        try:
            import xlsxwriter

            workbook = xlsxwriter.Workbook(buffer)
            worksheet = workbook.add_worksheet("Pedidos")

            NUM_COLS = 7
            HEADER_ROW = 2
            DATA_START = 3
            DATE_COLS = {3, 4}  # Data, PrazoEntrega
            VALOR_COL = 6  # ValorTotal

            # ── Formatos ────────────────────────────────────────────────────────
            fmt_title = workbook.add_format(
                {
                    "bold": True,
                    "font_size": 14,
                    "font_color": "#1E88E5",
                    "align": "center",
                    "valign": "vcenter",
                }
            )
            fmt_subtitle = workbook.add_format(
                {
                    "italic": True,
                    "font_size": 9,
                    "font_color": "#757575",
                    "align": "left",
                    "valign": "vcenter",
                }
            )
            # Cabeçalho de coluna — azul sólido, branco, bold
            fmt_hdr = workbook.add_format(
                {
                    "bold": True,
                    "font_size": 10,
                    "font_color": "#FFFFFF",
                    "bg_color": "#1E88E5",
                    "align": "center",
                    "valign": "vcenter",
                    "border": 1,
                    "border_color": "#BDBDBD",
                }
            )

            def _make_fmt(bg, align="left", bold=False, num_format=None):
                props = {
                    "font_size": 9,
                    "bg_color": bg,
                    "border": 1,
                    "border_color": "#BDBDBD",
                    "align": align,
                    "valign": "vcenter",
                }
                if bold:
                    props["bold"] = True
                if num_format:
                    props["num_format"] = num_format
                return workbook.add_format(props)

            # Par (branco) / ímpar (cinza) — texto
            fd0 = _make_fmt("#FFFFFF")
            fd1 = _make_fmt("#F5F5F5")
            # Par / ímpar — datas (centralizado)
            fdate0 = _make_fmt("#FFFFFF", align="center")
            fdate1 = _make_fmt("#F5F5F5", align="center")
            # Par / ímpar — ValorTotal (moeda, direita)
            MOEDA = '"R$ "#,##0.00'
            fval0 = _make_fmt("#FFFFFF", align="right", num_format=MOEDA)
            fval1 = _make_fmt("#F5F5F5", align="right", num_format=MOEDA)
            # Linha de total
            ftot_empty = _make_fmt("#E3F2FD", bold=True)
            ftot_label = _make_fmt("#E3F2FD", align="right", bold=True)
            ftot_valor = _make_fmt(
                "#E3F2FD", align="right", bold=True, num_format=MOEDA
            )

            # ── Larguras das colunas ─────────────────────────────────────────────
            for col_idx, width in enumerate([12, 40, 25, 14, 16, 22, 16]):
                worksheet.set_column(col_idx, col_idx, width)

            # ── Título e data ────────────────────────────────────────────────────
            worksheet.merge_range(
                0, 0, 0, NUM_COLS - 1, "Relatórios - Relatório de Pedidos", fmt_title
            )
            worksheet.set_row(0, 24)

            worksheet.merge_range(
                1,
                0,
                1,
                NUM_COLS - 1,
                f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                fmt_subtitle,
            )
            worksheet.set_row(1, 16)

            # ── Cabeçalhos ───────────────────────────────────────────────────────
            headers = [
                "Código",
                "Cliente",
                "Vendedor",
                "Data",
                "Prazo Entrega",
                "Situação",
                "Valor Total",
            ]
            col_keys = [
                "Codigo",
                "ClienteNome",
                "VendedorNome",
                "Data",
                "PrazoEntrega",
                "SituacaoNome",
                "ValorTotal",
            ]
            for col_idx, header in enumerate(headers):
                worksheet.write(HEADER_ROW, col_idx, header, fmt_hdr)
            worksheet.set_row(HEADER_ROW, 20)

            # ── Linhas de dados ──────────────────────────────────────────────────
            for i, (_, row) in enumerate(df.iterrows()):
                excel_row = DATA_START + i
                alt = i % 2 == 1

                for col_idx, col_key in enumerate(col_keys):
                    value = row.get(col_key, "")

                    if col_idx == VALOR_COL:
                        fmt = fval1 if alt else fval0
                        try:
                            worksheet.write_number(
                                excel_row, col_idx, float(value), fmt
                            )
                        except (ValueError, TypeError):
                            worksheet.write_number(excel_row, col_idx, 0.0, fmt)
                    elif col_idx in DATE_COLS:
                        fmt = fdate1 if alt else fdate0
                        worksheet.write(
                            excel_row, col_idx, str(value) if value else "", fmt
                        )
                    else:
                        fmt = fd1 if alt else fd0
                        worksheet.write(
                            excel_row, col_idx, str(value) if value else "", fmt
                        )

                worksheet.set_row(excel_row, 16)

            # ── Linha de total ───────────────────────────────────────────────────
            total_row = DATA_START + len(df)
            total_valor = (
                float(df["ValorTotal"].sum()) if "ValorTotal" in df.columns else 0.0
            )
            for col_idx in range(NUM_COLS):
                if col_idx < NUM_COLS - 2:
                    worksheet.write(total_row, col_idx, "", ftot_empty)
                elif col_idx == NUM_COLS - 2:
                    worksheet.write(total_row, col_idx, "TOTAL:", ftot_label)
                else:
                    worksheet.write_number(total_row, col_idx, total_valor, ftot_valor)
            worksheet.set_row(total_row, 18)

            workbook.close()
            return buffer.getvalue()

        except Exception as e:
            st.error(f"❌ Erro ao gerar Excel: {str(e)}")
            self.logger.error(f"Erro ao gerar Excel: {str(e)}")
            self.logger.error(traceback.format_exc())
            # Fallback: Excel simples sem formatação
            try:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    df.to_excel(writer, index=False, sheet_name="Pedidos")
                return buffer.getvalue()
            except Exception:
                return None

    def _generate_pdf(self, df: pd.DataFrame) -> bytes:
        """Gera PDF do relatório de pedidos usando reportlab"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )

            buffer = io.BytesIO()

            doc = SimpleDocTemplate(
                buffer,
                pagesize=landscape(A4),
                rightMargin=1 * cm,
                leftMargin=1 * cm,
                topMargin=1.5 * cm,
                bottomMargin=1 * cm,
            )

            styles = getSampleStyleSheet()
            elements = []

            # Título e data de geração
            elements.append(Paragraph("Relatórios - Relatório de Pedidos", styles["Title"]))
            elements.append(
                Paragraph(
                    f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    styles["Normal"],
                )
            )
            elements.append(Spacer(1, 0.5 * cm))

            # Cabeçalho da tabela
            headers = [
                "Código",
                "Cliente",
                "Vendedor",
                "Data",
                "Prazo Entrega",
                "Situação",
                "Valor Total",
            ]
            table_data = [headers]

            # Linhas de dados
            for _, row in df.iterrows():
                valor_fmt = f"R$ {self._format_br(float(row.get('ValorTotal', 0)))}"
                table_row = [
                    str(row.get("Codigo", "")),
                    str(row.get("ClienteNome", ""))[:45],
                    str(row.get("VendedorNome", ""))[:25],
                    str(row.get("Data", "")),
                    str(row.get("PrazoEntrega", "")),
                    str(row.get("SituacaoNome", ""))[:22],
                    valor_fmt,
                ]
                table_data.append(table_row)

            # Linha de total
            total_valor = df["ValorTotal"].sum() if "ValorTotal" in df.columns else 0.0
            total_fmt = f"R$ {self._format_br(total_valor)}"
            table_data.append(["", "", "", "", "", "TOTAL:", total_fmt])

            # Larguras das colunas (paisagem A4 ≈ 27,7 cm útil)
            col_widths = [
                2.5 * cm,
                6.5 * cm,
                4.5 * cm,
                2.5 * cm,
                3 * cm,
                3.5 * cm,
                3.2 * cm,
            ]

            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        # Cabeçalho
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E88E5")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        # Dados
                        ("FONTSIZE", (0, 1), (-1, -2), 8),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -2),
                            [colors.white, colors.HexColor("#F5F5F5")],
                        ),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        # Linha de total
                        (
                            "BACKGROUND",
                            (0, -1),
                            (-1, -1),
                            colors.HexColor("#E3F2FD"),
                        ),
                        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, -1), (-1, -1), 8),
                        # Alinhamento numérico
                        ("ALIGN", (6, 0), (6, -1), "RIGHT"),
                        ("ALIGN", (3, 1), (4, -1), "CENTER"),
                    ]
                )
            )

            elements.append(table)
            doc.build(elements)
            return buffer.getvalue()

        except ImportError:
            st.warning(
                "⚠️ Biblioteca 'reportlab' não encontrada. "
                "Instale com: pip install reportlab"
            )
            return None
        except Exception as e:
            st.error(f"❌ Erro ao gerar PDF: {str(e)}")
            self.logger.error(f"Erro ao gerar PDF: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None

    def _render_data_table(self):
        """Renderiza tabela de pedidos com AgGrid e botões de exportação"""
        df = st.session_state.pedidos_df

        if df is None or df.empty:
            return

        st.subheader("📋 Pedidos")

        total_valor = df["ValorTotal"].sum() if "ValorTotal" in df.columns else 0.0

        # Métricas e botões de exportação
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

        with col1:
            st.metric("📋 Total Pedidos", len(df))
        with col2:
            st.metric("💰 Valor Total", f"R$ {self._format_br(total_valor)}")
        with col3:
            # Exportar para Excel (formatado no mesmo padrão do PDF)
            excel_data = self._generate_excel(df)
            if excel_data:
                st.download_button(
                    label="📊 Excel",
                    data=excel_data,
                    file_name=f"pedidos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    help="Exportar relatório para Excel",
                )
        with col4:
            # Exportar para PDF
            pdf_data = self._generate_pdf(df)
            if pdf_data:
                st.download_button(
                    label="📄 PDF",
                    data=pdf_data,
                    file_name=f"pedidos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    help="Exportar relatório para PDF",
                )

        st.markdown("---")

        # Grid AgGrid
        try:
            from st_aggrid import AgGrid, GridOptionsBuilder

            df_display = df.copy()

            gb = GridOptionsBuilder.from_dataframe(df_display)
            gb.configure_grid_options(
                domLayout="normal",
                enableRangeSelection=True,
                enableCellTextSelection=True,
                suppressRowClickSelection=True,
            )

            # Configurações de coluna padrão — mesmo padrão do relatório de vendas
            gb.configure_default_column(
                filter=True,
                cellStyle={"border": "1px solid black"},
                floatingFilter=True,
                sortable=True,
            )

            # Configuração personalizada por coluna
            gb.configure_column("Codigo", headerName="Código", width=120)
            gb.configure_column("ClienteNome", headerName="Cliente", width=250)
            gb.configure_column("VendedorNome", headerName="Vendedor", width=200)
            gb.configure_column(
                "Data",
                headerName="Data",
                type=["dateColumnFilter"],
                width=120,
            )
            gb.configure_column(
                "PrazoEntrega",
                headerName="Prazo Entrega",
                type=["dateColumnFilter"],
                width=140,
            )
            gb.configure_column("SituacaoNome", headerName="Situação", width=160)
            gb.configure_column(
                "ValorTotal",
                headerName="Valor Total",
                type=["numericColumn", "numberColumnFilter"],
                valueFormatter=(
                    "'R$ ' + x.toLocaleString('pt-BR', "
                    "{minimumFractionDigits: 2, maximumFractionDigits: 2})"
                ),
                width=150,
            )

            grid_options = gb.build()

            # Key dinâmica baseada no contador de carregamentos.
            # Quando os dados mudam, a key muda → AgGrid recria o componente
            # com os novos dados, evitando cache visual desatualizado.
            grid_key = f"pedidos_grid_{st.session_state.get('pedidos_load_count', 0)}"
            AgGrid(
                df_display,
                gridOptions=grid_options,
                height=400,
                fit_columns_on_grid_load=True,
                theme="alpine",
                allow_unsafe_jscode=True,
                update_mode="MODEL_CHANGED",
                key=grid_key,
            )

        except ImportError:
            st.error(
                "❌ AgGrid não está instalado. Instale com: pip install streamlit-aggrid"
            )
            st.dataframe(df.head(100), use_container_width=True)
        except Exception as e:
            st.error(f"❌ Erro ao exibir tabela: {str(e)}")
            self.logger.error(f"Erro ao renderizar grid: {str(e)}")
            self.logger.error(traceback.format_exc())
            st.dataframe(df.head(100), use_container_width=True)


def main(key=None):
    """
    Função principal do módulo Relatório de Pedidos (compatível com app.py)

    Args:
        key: Chave única para o módulo (requerido pela aplicação principal)
    """
    try:
        controller = PedidosController()
        controller.render_dashboard()
    except Exception as e:
        st.error("❌ Erro fatal no módulo Pedidos")
        st.error(str(e))
        logging.error(f"Erro fatal no módulo Pedidos: {str(e)}")


# Para execução direta (desenvolvimento)
if __name__ == "__main__":
    main()
