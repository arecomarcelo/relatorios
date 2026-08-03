"""
SGR - Módulo de Recebimentos
Relatório de Recebimentos a Vencer
"""

import io
import logging
import traceback
from datetime import date, datetime

import pandas as pd
import streamlit as st

# Imports da aplicação
try:
    from core.container_recebimentos import DIContainerRecebimentos
    from core.exceptions import BusinessLogicError, SGRException, ValidationError
    from presentation.styles.theme_simple import apply_theme
except ImportError as e:
    st.error(f"❌ Erro crítico de importação: {e}")
    st.stop()


class RecebimentosController:
    """Controller de recebimentos"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.container = None
        self.recebimentos_service = None

        # Inicializar serviços
        self._initialize_services()

    def _initialize_services(self):
        """Inicializa serviços com tratamento de erro"""
        try:
            self.container = DIContainerRecebimentos()
            self.recebimentos_service = self.container.get_recebimentos_service()
            self.logger.info("Serviços de recebimentos inicializados com sucesso")

        except Exception as e:
            self.logger.error(f"Erro na inicialização: {str(e)}")
            st.error(f"❌ Erro na inicialização: {str(e)}")
            st.error("Verifique a configuração do banco de dados em config/settings.py")
            st.stop()

    def render_dashboard(self):
        """Renderiza dashboard principal de recebimentos"""
        try:
            # Verificar se está no modo manual
            if st.session_state.get("recebimentos_view_mode") == "manual":
                self._render_manual_fullscreen()
                return

            # Aplicar tema
            apply_theme()

            # Header
            st.markdown(
                "<h1 style='text-align: center; color: #1E88E5;'>💰 Relatórios - Relatório de Recebimentos</h1>",
                unsafe_allow_html=True,
            )

            # Botão Ler Manual centralizado abaixo do título
            col1, col2, col3 = st.columns([2, 1, 2])
            with col2:
                if st.button(
                    "📖 Ler Manual",
                    type="secondary",
                    use_container_width=True,
                    help="Clique para ler o manual completo do Relatório de Recebimentos",
                ):
                    st.session_state["recebimentos_view_mode"] = "manual"
                    st.rerun()

            st.markdown("---")

            # Verificar saúde do sistema
            if not self._health_check():
                return

            # Renderizar seções
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

    def _health_check(self) -> bool:
        """Verifica saúde do sistema"""
        try:
            health = self.container.health_check()

            if all(health.values()):
                # Sistema funcionando normalmente (mensagem removida)
                return True
            else:
                failed_services = [k for k, v in health.items() if not v]
                st.error(f"❌ Serviços com problemas: {', '.join(failed_services)}")
                return False

        except Exception as e:
            st.error(f"❌ Erro no health check: {str(e)}")
            return False

    def _render_manual_fullscreen(self):
        """Renderiza o manual em tela cheia"""
        try:
            # Aplicar tema
            apply_theme()

            # Ler arquivo do manual primeiro
            manual_path = "documentacao/Manual_Relatorio_Recebimentos.md"
            with open(manual_path, "r", encoding="utf-8") as file:
                content = file.read()

            # CSS para melhorar alinhamento e aparência dos botões
            st.markdown(
                """
            <style>
            .manual-header {
                display: flex;
                justify-content: center;
                align-items: center;
                margin-bottom: 2rem;
                gap: 1rem;
            }

            .manual-title {
                text-align: center;
                color: #1E88E5;
                margin: 0;
                font-size: 2rem;
                font-weight: 600;
            }

            .manual-buttons {
                display: flex;
                gap: 0.5rem;
                align-items: center;
            }

            /* Alinhar botões corretamente */
            div[data-testid="column"] .stDownloadButton,
            div[data-testid="column"] .stButton {
                display: flex;
                align-items: center;
                justify-content: center;
                margin-top: 0.5rem;
            }

            div[data-testid="column"] .stDownloadButton > button,
            div[data-testid="column"] .stButton > button {
                height: 2.5rem;
                font-size: 0.9rem;
                font-weight: 500;
                border-radius: 0.5rem;
                margin: 0;
            }
            </style>
            """,
                unsafe_allow_html=True,
            )

            # Header com layout melhorado
            st.markdown(
                '<div class="manual-header">'
                '<h1 class="manual-title">📖 Manual do Relatório de Recebimentos</h1>'
                "</div>",
                unsafe_allow_html=True,
            )

            # Botões de ação centralizados
            col1, col2, col3, col4, col5 = st.columns([2, 1.5, 0.5, 1.5, 2])

            with col2:
                st.download_button(
                    label="📥 Download Manual",
                    data=content,
                    file_name="Manual_Relatorio_Recebimentos.md",
                    mime="text/markdown",
                    key="download_manual_recebimentos",
                    use_container_width=True,
                )

            with col4:
                if st.button(
                    "⬅️ Voltar ao Dashboard",
                    key="back_to_recebimentos_dashboard",
                    use_container_width=True,
                ):
                    st.session_state["recebimentos_view_mode"] = "dashboard"
                    st.rerun()

            st.markdown("---")

            # Exibir conteúdo do manual diretamente
            st.markdown(content)

        except FileNotFoundError:
            st.error(
                f"❌ Arquivo do manual não encontrado: documentacao/Manual_Relatorio_Recebimentos.md"
            )
            # Botão para voltar mesmo com erro
            if st.button("⬅️ Voltar ao Dashboard", key="back_error"):
                st.session_state["recebimentos_view_mode"] = "dashboard"
                st.rerun()
        except Exception as e:
            st.error(f"❌ Erro ao carregar manual: {str(e)}")
            # Botão para voltar mesmo com erro
            if st.button("⬅️ Voltar ao Dashboard", key="back_error2"):
                st.session_state["recebimentos_view_mode"] = "dashboard"
                st.rerun()

    def _render_filters_and_data(self):
        """Renderiza filtros e dados"""
        st.subheader("🔍 Filtros e Dados")

        # Inicializar dados na sessão
        if "recebimentos_df" not in st.session_state:
            st.session_state.recebimentos_df = None
        if "recebimentos_metricas" not in st.session_state:
            st.session_state.recebimentos_metricas = None
        if "recebimentos_auto_loaded" not in st.session_state:
            st.session_state.recebimentos_auto_loaded = False

        # Carregar dados do mês atual automaticamente na primeira vez
        if (
            not st.session_state.recebimentos_auto_loaded
            and st.session_state.recebimentos_df is None
        ):
            try:
                with st.spinner("Carregando dados do mês atual..."):
                    df_recebimentos = (
                        self.recebimentos_service.get_recebimentos_mes_atual()
                    )
                    metricas = self.recebimentos_service.get_metricas_recebimentos(
                        df_recebimentos
                    )

                    # Adicionar período filtrado às métricas
                    hoje = datetime.now().date()
                    primeiro_dia_mes = date(hoje.year, hoje.month, 1)
                    metricas[
                        "periodo_filtrado"
                    ] = f"{primeiro_dia_mes.strftime('%d/%m/%Y')} a {hoje.strftime('%d/%m/%Y')}"

                st.session_state.recebimentos_df = df_recebimentos
                st.session_state.recebimentos_metricas = metricas
                st.session_state.recebimentos_filtro_key = (
                    f"{primeiro_dia_mes}_{hoje}_{len(df_recebimentos)}"
                )
                st.session_state.recebimentos_auto_loaded = True

                if not df_recebimentos.empty:
                    st.rerun()
            except Exception as e:
                self.logger.error(f"Erro ao carregar dados iniciais: {str(e)}")
                st.session_state.recebimentos_auto_loaded = True  # Marcar como tentado

        # Seção de filtros
        with st.expander("Configurar Filtros", expanded=True):
            self._render_filters()

        # Exibir métricas e dados
        if st.session_state.recebimentos_df is not None:
            self._render_metrics()
            self._render_data_table()
        else:
            st.info(
                "ℹ️ **Nenhum dado carregado ainda.**\n\n"
                "👆 Use os botões acima para:\n"
                "- **🔍 Aplicar Filtros**: Carregar dados com período personalizado\n"
                "- **📅 Dados do Mês Atual**: Carregar dados do mês corrente rapidamente"
            )

    def _render_filters(self):
        """Renderiza seção de filtros"""
        try:
            # Obter datas padrão (1º dia do mês até hoje)
            hoje = datetime.now().date()
            primeiro_dia_mes = date(hoje.year, hoje.month, 1)

            col1, col2 = st.columns(2)

            with col1:
                data_inicio = st.date_input(
                    "Data Inicial",
                    value=primeiro_dia_mes,
                    format="DD/MM/YYYY",
                    help="Data inicial do período de recebimentos",
                )

            with col2:
                data_fim = st.date_input(
                    "Data Final",
                    value=hoje,
                    format="DD/MM/YYYY",
                    help="Data final do período de recebimentos",
                )

            # Botões de ação - alinhados à esquerda
            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button(
                    "🔍 Aplicar Filtros", type="primary", use_container_width=True
                ):
                    self._apply_filters(data_inicio, data_fim)

            with col2:
                if st.button("📅 Dados do Mês Atual", use_container_width=True):
                    self._load_current_month_data()

        except Exception as e:
            st.error(f"❌ Erro nos filtros: {str(e)}")

    def _apply_filters(self, data_inicio: date, data_fim: date):
        """Aplica filtros e carrega dados"""
        try:
            # Validar filtros
            if not data_inicio or not data_fim:
                st.error("❌ Datas inicial e final são obrigatórias")
                return

            if data_inicio > data_fim:
                st.error("❌ Data inicial não pode ser maior que data final")
                return

            # Verificar se período é maior que 365 dias (aviso, não bloqueia)
            diff_days = (data_fim - data_inicio).days
            if diff_days > 365:
                st.warning("⚠️ Período muito longo pode afetar a performance")

            # Carregar dados
            spinner_message = (
                "⏳ Carregando dados de recebimentos..."
                if diff_days > 365
                else "Carregando dados de recebimentos..."
            )
            with st.spinner(spinner_message):
                df_recebimentos = self.recebimentos_service.get_recebimentos_filtrados(
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                )

            # Calcular métricas
            with st.spinner("Calculando métricas..."):
                metricas = self.recebimentos_service.get_metricas_recebimentos(
                    df_recebimentos
                )
                # Adicionar período filtrado às métricas
                metricas[
                    "periodo_filtrado"
                ] = f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"

            # Armazenar na sessão
            st.session_state.recebimentos_df = df_recebimentos
            st.session_state.recebimentos_metricas = metricas
            # Chave única para forçar atualização da grid
            st.session_state.recebimentos_filtro_key = (
                f"{data_inicio}_{data_fim}_{len(df_recebimentos)}"
            )

            if df_recebimentos.empty:
                st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados")
            else:
                st.success(f"✅ {len(df_recebimentos)} registros carregados com sucesso")
                st.rerun()

        except ValidationError as e:
            st.error(f"❌ Erro de validação: {str(e)}")
        except BusinessLogicError as e:
            st.error(f"❌ Erro de negócio: {str(e)}")
        except Exception as e:
            st.error(f"❌ Erro ao aplicar filtros: {str(e)}")
            self.logger.error(f"Erro ao aplicar filtros: {str(e)}")

    def _load_current_month_data(self):
        """Carrega dados do mês atual"""
        try:
            with st.spinner("Carregando dados do mês atual..."):
                df_recebimentos = self.recebimentos_service.get_recebimentos_mes_atual()
                metricas = self.recebimentos_service.get_metricas_recebimentos(
                    df_recebimentos
                )

                # Adicionar período filtrado às métricas
                hoje = datetime.now().date()
                primeiro_dia_mes = date(hoje.year, hoje.month, 1)
                metricas[
                    "periodo_filtrado"
                ] = f"{primeiro_dia_mes.strftime('%d/%m/%Y')} a {hoje.strftime('%d/%m/%Y')}"

            st.session_state.recebimentos_df = df_recebimentos
            st.session_state.recebimentos_metricas = metricas
            # Chave única para forçar atualização da grid
            st.session_state.recebimentos_filtro_key = (
                f"{primeiro_dia_mes}_{hoje}_{len(df_recebimentos)}"
            )

            st.success(f"✅ {len(df_recebimentos)} recebimentos do mês atual carregados")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Erro ao carregar dados do mês atual: {str(e)}")

    def _render_metrics(self):
        """Renderiza métricas em cards"""
        if st.session_state.recebimentos_metricas:
            st.subheader("📊 Métricas de Recebimento")

            metricas = st.session_state.recebimentos_metricas

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "📅 Período Filtrado",
                    metricas.get("periodo_filtrado", "N/A"),
                )

            with col2:
                st.metric(
                    "📋 Total de Recebimentos",
                    f"{metricas.get('total_quantidade', 0):,}",
                )

            with col3:
                valor_total = metricas.get("total_valor", 0.0)
                # Formatação européia/brasileira: 601.539,43
                valor_formatado = (
                    f"R$ {valor_total:,.2f}".replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )
                st.metric(
                    "💰 Valor Total",
                    valor_formatado,
                )

            st.markdown("---")

    def _create_formatted_excel(self, df: pd.DataFrame) -> io.BytesIO:
        """
        Cria arquivo Excel formatado de forma elegante

        Args:
            df: DataFrame com os dados a exportar

        Returns:
            BytesIO: Buffer com o arquivo Excel formatado
        """
        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Recebimentos", startrow=1)

            workbook = writer.book
            worksheet = writer.sheets["Recebimentos"]

            # Definir formatos
            # Formato do cabeçalho
            header_format = workbook.add_format(
                {
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'vcenter',
                    'align': 'center',
                    'fg_color': '#1E88E5',
                    'font_color': 'white',
                    'border': 1,
                    'font_size': 11,
                }
            )

            # Formato de data
            date_format = workbook.add_format(
                {'num_format': 'dd/mm/yyyy', 'align': 'center', 'border': 1}
            )

            # Formato monetário (R$)
            money_format = workbook.add_format(
                {'num_format': 'R$ #,##0.00', 'border': 1}
            )

            # Formato de texto normal
            text_format = workbook.add_format({'border': 1, 'valign': 'vcenter'})

            # Formato de célula alternada (zebra)
            alt_format = workbook.add_format(
                {'bg_color': '#F5F5F5', 'border': 1, 'valign': 'vcenter'}
            )

            # Formato de totais
            total_format = workbook.add_format(
                {'bold': True, 'bg_color': '#E3F2FD', 'border': 1, 'font_size': 11}
            )

            total_money_format = workbook.add_format(
                {
                    'bold': True,
                    'bg_color': '#E3F2FD',
                    'num_format': 'R$ #,##0.00',
                    'border': 1,
                    'font_size': 11,
                }
            )

            # Adicionar título
            title_format = workbook.add_format(
                {
                    'bold': True,
                    'font_size': 14,
                    'fg_color': '#1976D2',
                    'font_color': 'white',
                    'align': 'center',
                    'valign': 'vcenter',
                    'border': 1,
                }
            )

            # Mesclar células para o título
            worksheet.merge_range(
                'A1:D1', '💰 Relatório de Recebimentos - Relatórios', title_format
            )

            # Escrever cabeçalhos com formatação
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(1, col_num, value, header_format)

            # Aplicar formatos às colunas
            num_rows = len(df)

            for row_num in range(num_rows):
                row_data = df.iloc[row_num]

                # Formato alternado (zebra)
                row_format = alt_format if row_num % 2 == 0 else text_format

                for col_num, col_name in enumerate(df.columns):
                    value = row_data[col_name]

                    if col_name == "Vencimento":
                        # Formatação de data
                        worksheet.write(row_num + 2, col_num, value, date_format)
                    elif col_name == "Valor":
                        # Formatação monetária
                        worksheet.write(row_num + 2, col_num, value, money_format)
                    elif col_name == "FormaPagamento":
                        # Texto normal
                        worksheet.write(row_num + 2, col_num, value, row_format)
                    elif col_name == "Cliente":
                        # Texto normal
                        worksheet.write(row_num + 2, col_num, value, row_format)

            # Adicionar linha de totais
            total_row = num_rows + 2
            worksheet.write(total_row, 0, "TOTAL", total_format)
            worksheet.write(total_row, 1, df["Valor"].sum(), total_money_format)
            worksheet.write(
                total_row, 2, "", total_format
            )  # FormaPagamento vazio no total
            worksheet.write(total_row, 3, f"{len(df)} recebimentos", total_format)

            # Ajustar largura das colunas
            worksheet.set_column('A:A', 15)  # Vencimento
            worksheet.set_column('B:B', 18)  # Valor
            worksheet.set_column('C:C', 25)  # FormaPagamento
            worksheet.set_column('D:D', 50)  # Cliente

            # Congelar painéis (cabeçalho fixo)
            worksheet.freeze_panes(2, 0)

        buffer.seek(0)
        return buffer

    def _render_data_table(self):
        """Renderiza tabela de dados usando AgGrid"""
        df = st.session_state.recebimentos_df

        if df is None or df.empty:
            return

        st.subheader("📋 Dados Detalhados")

        # Preparar dados para exibição
        try:
            from st_aggrid import AgGrid, GridOptionsBuilder

            df_display = df.copy()

            # Função para limpar e converter valores monetários
            def clean_monetary_value(val):
                """Remove formatação monetária e converte para float"""
                if pd.isna(val):
                    return 0.0
                if isinstance(val, (int, float)):
                    return float(val)
                # Converter para string e limpar
                val_str = str(val).replace("R$", "").strip()

                # Se tem vírgula, é formato brasileiro (1.500,00)
                if "," in val_str:
                    val_clean = val_str.replace(".", "").replace(",", ".")
                else:
                    val_clean = val_str

                val_clean = val_clean.strip()
                try:
                    return float(val_clean) if val_clean else 0.0
                except:
                    return 0.0

            # Garantir que valores monetários sejam float
            if "Valor" in df_display.columns:
                df_display["Valor"] = df_display["Valor"].apply(clean_monetary_value)

            # Configurar AgGrid
            gb = GridOptionsBuilder.from_dataframe(df_display)

            gb.configure_grid_options(
                domLayout="normal",
                enableRangeSelection=True,
                enableCellTextSelection=True,
                suppressRowClickSelection=True,
            )

            # Configurações de coluna padrão
            gb.configure_default_column(
                filter=True,
                cellStyle={"border": "1px solid black"},
                floatingFilter=True,
                sortable=True,
            )

            # Configuração personalizada por coluna
            for col in df_display.columns:
                if col == "Vencimento":
                    gb.configure_column(
                        col,
                        headerName="Vencimento",
                        width=130,
                    )
                elif col == "Valor":
                    gb.configure_column(
                        col,
                        headerName="Valor",
                        type=["numericColumn", "numberColumnFilter"],
                        valueFormatter="'R$ ' + x.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})",
                        width=130,
                    )
                elif col == "FormaPagamento":
                    gb.configure_column(col, headerName="Forma de Pagamento", width=180)
                elif col == "Cliente":
                    gb.configure_column(col, headerName="Cliente", width=300)
                else:
                    gb.configure_column(col, headerName=col)

            grid_options = gb.build()

            # Gerar chave única baseada nos filtros para forçar atualização da grid
            grid_key = st.session_state.get(
                "recebimentos_filtro_key", "recebimentos_grid_default"
            )

            # Renderizar AgGrid
            grid_response = AgGrid(
                df_display,
                gridOptions=grid_options,
                height=400,
                fit_columns_on_grid_load=True,
                theme="alpine",
                allow_unsafe_jscode=True,
                update_mode="MODEL_CHANGED",
                key=f"recebimentos_grid_{grid_key}",
            )

            # Seção de download
            st.markdown("---")
            st.subheader("📥 Download dos Dados")
            col1, col2 = st.columns(2)

            with col1:
                # Download CSV
                csv_data = df_display.to_csv(index=False)
                st.download_button(
                    label="📄 Download CSV",
                    data=csv_data,
                    file_name=f"recebimentos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with col2:
                # Download Excel formatado
                buffer = self._create_formatted_excel(df_display)
                st.download_button(
                    label="📊 Download Excel",
                    data=buffer.getvalue(),
                    file_name=f"recebimentos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.ms-excel",
                    use_container_width=True,
                )

        except ImportError:
            st.error(
                "❌ AgGrid não está instalado. Instale com: pip install streamlit-aggrid"
            )
            # Fallback: mostrar dataframe básico
            st.dataframe(df.head(100), use_container_width=True)
        except Exception as e:
            st.error(f"❌ Erro ao exibir tabela: {str(e)}")
            self.logger.error(f"Erro ao renderizar grid: {str(e)}")
            # Fallback: mostrar dataframe básico
            st.dataframe(df.head(100), use_container_width=True)


def main(key=None):
    """
    Função principal do módulo de recebimentos

    Args:
        key: Chave única para o módulo (requerido pela aplicação principal)
    """
    try:
        # Criar e executar controller
        controller = RecebimentosController()
        controller.render_dashboard()

    except Exception as e:
        st.error("❌ Erro fatal no módulo de recebimentos")
        st.error(str(e))
        logging.error(f"Erro fatal no módulo de recebimentos: {str(e)}")


# Para execução direta (desenvolvimento)
if __name__ == "__main__":
    main()
