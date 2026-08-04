"""
Relatórios - Módulo Vendas - Relatório Comparativo Anual
Compara métricas de Vendas do mês selecionado entre o ano anterior e o ano atual
"""

import calendar
import logging
import traceback
from datetime import date

import pandas as pd
import streamlit as st

# Imports da aplicação
try:
    from core.container_vendas import DIContainer
    from core.exceptions import BusinessLogicError, ValidationError
    from presentation.styles.theme_simple import apply_theme
except ImportError as e:
    st.error(f"❌ Erro crítico de importação: {e}")
    st.stop()


MESES_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

# Cards de Métricas de Vendas — mesmo padrão do Relatório Comercial (_render_metrics_cards)
# (label, campo no dict de métricas, formato: True=moeda, "pct"=percentual, False=inteiro)
# A pedido do usuário, somente 💎 Valor Total fica visível (destaque único); os demais
# ficam ocultos aqui, comentados para reativação futura caso necessário.
CARDS_METRICAS_VENDAS = [
    # ("💰 Total Entradas", "total_entradas", True),
    # ("⏳ Total Parcelado", "total_parcelado", True),
    ("💎 Valor Total", "total_valor", True),
    # ("📊 Total de Vendas", "total_quantidade", False),
    # ("🎯 Ticket Médio", "ticket_medio", True),
    # ("📈 Margem Média", "margem_media", "pct"),
]

class ComparativoController:
    """Controller para o Relatório Comparativo Anual de vendas"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.container = None
        self.vendas_service = None
        self._initialize_services()

    def _initialize_services(self):
        """Inicializa serviços com tratamento de erro"""
        try:
            self.container = DIContainer()
            self.vendas_service = self.container.get_vendas_service()
            self.logger.info(
                "Serviços de vendas (Comparativo) inicializados com sucesso"
            )
        except Exception as e:
            self.logger.error(f"Erro na inicialização: {str(e)}")
            st.error(f"❌ Erro na inicialização: {str(e)}")
            st.error("Verifique a configuração do banco de dados em config/settings.py")
            st.stop()

    def render_dashboard(self):
        """Renderiza o dashboard do Relatório Comparativo Anual"""
        try:
            apply_theme()

            st.markdown(
                "<h1 style='text-align: center; color: #1E88E5;'>📊 Relatórios - Comparativo Anual</h1>",
                unsafe_allow_html=True,
            )
            st.markdown("---")

            self._render_update_info()
            self._render_filters()

            mes_aplicado = st.session_state.get("comparativo_mes_aplicado")
            if mes_aplicado:
                self._render_comparativo(mes_aplicado)
            else:
                st.info(
                    "ℹ️ Selecione o **Mês** acima e clique em **✅ Aplicar** para "
                    "visualizar o comparativo entre o ano anterior e o ano atual."
                )

        except Exception as e:
            self.logger.error(f"Erro no dashboard Comparativo: {str(e)}")
            self.logger.error(traceback.format_exc())
            st.error("❌ Erro inesperado no dashboard. Verifique os logs.")
            with st.expander(
                "🔍 Detalhes do erro (clique para expandir)", expanded=True
            ):
                st.code(traceback.format_exc())
                st.error(f"Tipo de erro: {type(e).__name__}")
                st.error(f"Mensagem: {str(e)}")

    def _render_update_info(self):
        """Renderiza informações de atualização (Data e Hora da última sincronização)"""
        try:
            with st.expander("🔄 Informações de Atualização", expanded=False):
                info = self.vendas_service.get_informacoes_atualizacao()

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📅 Data", info.get("data", "N/A"))
                with col2:
                    st.metric("⏰ Hora", info.get("hora", "N/A"))

        except Exception as e:
            self.logger.warning(
                f"Erro ao carregar informações de atualização: {str(e)}"
            )

    def _render_filters(self):
        """Renderiza o filtro de Mês e o botão Aplicar — estreitos e alinhados à esquerda"""
        st.subheader("🔍 Filtros")

        col1, col2, _spacer = st.columns([1.3, 1, 3.7])
        with col1:
            mes_nome = st.selectbox(
                "📆 Mês",
                options=list(MESES_PT.values()),
                index=date.today().month - 1,
                help="Mês a comparar entre o ano anterior e o ano atual",
                key="comparativo_mes_select",
            )
        with col2:
            st.markdown("<div style='height: 1.8rem'></div>", unsafe_allow_html=True)
            aplicar = st.button(
                "✅ Aplicar",
                type="primary",
                use_container_width=True,
                key="btn_aplicar_comparativo",
                help="Carregar o comparativo do mês selecionado",
            )

        if aplicar:
            st.session_state["comparativo_mes_aplicado"] = mes_nome

    def _get_month_range(self, mes_numero: int, ano: int):
        """Retorna (data_inicio, data_fim) do mês/ano informado"""
        data_inicio = date(ano, mes_numero, 1)
        ultimo_dia = calendar.monthrange(ano, mes_numero)[1]
        data_fim = date(ano, mes_numero, ultimo_dia)
        return data_inicio, data_fim

    def _carregar_periodo(self, mes_numero: int, ano: int) -> dict:
        """Carrega métricas de Vendas para um mês/ano específico"""
        data_inicio, data_fim = self._get_month_range(mes_numero, ano)

        try:
            df_vendas = self.vendas_service.get_vendas_filtradas(
                data_inicio=data_inicio, data_fim=data_fim
            )
            metricas = self.vendas_service.get_metricas_vendas(df_vendas)
        except (ValidationError, BusinessLogicError) as e:
            # Ex.: mês/ano ainda no futuro em relação a hoje — sem dados a comparar
            self.logger.info(
                f"Sem dados de vendas para {mes_numero:02d}/{ano}: {str(e)}"
            )
            metricas = self.vendas_service.get_metricas_vendas(pd.DataFrame())

        return {"metricas": metricas}

    def _render_comparativo(self, mes_nome: str):
        """Carrega e renderiza o painel comparativo de Vendas"""
        mes_numero = list(MESES_PT.values()).index(mes_nome) + 1
        ano_atual = date.today().year
        ano_anterior = ano_atual - 1

        with st.spinner(
            f"Carregando dados de {mes_nome}/{ano_anterior} e {mes_nome}/{ano_atual}..."
        ):
            dados_anterior = self._carregar_periodo(mes_numero, ano_anterior)
            dados_atual = self._carregar_periodo(mes_numero, ano_atual)

        st.markdown("---")
        self._render_metricas_vendas_destaque(
            mes_nome=mes_nome,
            ano_anterior=ano_anterior,
            dados_anterior=dados_anterior["metricas"],
            dados_atual=dados_atual["metricas"],
        )

    def _calc_delta_pct(self, valor_anterior: float, valor_atual: float):
        """Calcula a variação percentual entre dois valores (None se não houver base)"""
        if not valor_anterior:
            return None
        return ((valor_atual - valor_anterior) / valor_anterior) * 100

    def _formatar_valor(self, valor: float, formato) -> str:
        """Formata o valor de um card conforme o tipo (moeda, percentual ou inteiro)"""
        if formato is True:
            return (
                f"R$ {valor:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
            )
        if formato == "pct":
            return f"{valor:.2f}%" if valor else "N/A"
        return f"{int(valor):,}".replace(",", ".")

    def _render_metricas_vendas_destaque(
        self,
        mes_nome: str,
        ano_anterior: int,
        dados_anterior: dict,
        dados_atual: dict,
    ):
        """Painel de Vendas reduzido a um único card em destaque (💎 Valor Total),
        centralizado e ampliado — os demais indicadores ficam ocultos."""
        st.markdown(
            f"<h3 style='text-align: center; color: #1E88E5;'>"
            f"💎 Métricas de Vendas — {mes_nome}</h3>",
            unsafe_allow_html=True,
        )

        label, campo, formato = CARDS_METRICAS_VENDAS[0]
        valor_ant = dados_anterior.get(campo, 0) or 0
        valor_atu = dados_atual.get(campo, 0) or 0
        delta_pct = self._calc_delta_pct(valor_ant, valor_atu)

        _esq, col_card, _dir = st.columns([1, 1.4, 1])
        with col_card:
            self._render_card_destaque(
                label=label,
                valor_fmt=self._formatar_valor(valor_atu, formato),
                sub_texto=f"{mes_nome}/{ano_anterior}: "
                f"{self._formatar_valor(valor_ant, formato)}",
                delta_pct=delta_pct,
            )

    def _render_card_destaque(self, label: str, valor_fmt: str, sub_texto: str, delta_pct):
        """Card único, centralizado e ampliado — mesma linguagem visual do
        Relatório Comercial, com tipografia maior para funcionar como destaque isolado."""
        if delta_pct is None:
            delta_html = (
                "<div style='font-size: 0.95rem; color: #9ca3af; margin-top: 8px;'>"
                "Sem base de comparação</div>"
            )
        else:
            cor = "#2e7d32" if delta_pct >= 0 else "#c62828"
            seta = "▲" if delta_pct >= 0 else "▼"
            delta_html = (
                f"<div style='font-size: 1.1rem; font-weight: 700; color: {cor}; "
                f"margin-top: 8px;'>{seta} {delta_pct:+.1f}%</div>"
            )

        st.markdown(
            f"""
        <div style='
            background: #ffffff;
            border-radius: 14px;
            padding: 28px;
            text-align: center;
            box-shadow: 0 6px 18px rgba(30, 136, 229, 0.2);
            font-family: Roboto, sans-serif;
            min-height: 170px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        '>
            <div style='font-size: 1.1rem; color: #1E88E5; margin-bottom: 10px; font-weight: 600;'>{label}</div>
            <div style='font-size: 2.2rem; font-weight: 800; color: #1E88E5;'>{valor_fmt}</div>
            <div style='font-size: 0.9rem; color: #6b7280; margin-top: 8px;'>{sub_texto}</div>
            {delta_html}
        </div>
        """,
            unsafe_allow_html=True,
        )

def main(key=None):
    """
    Função principal do módulo Relatório Comparativo (compatível com app.py)

    Args:
        key: Chave única para o módulo (requerido pela aplicação principal)
    """
    try:
        controller = ComparativoController()
        controller.render_dashboard()
    except Exception as e:
        st.error("❌ Erro fatal no módulo Comparativo")
        st.error(str(e))
        logging.error(f"Erro fatal no módulo Comparativo: {str(e)}")


# Para execução direta (desenvolvimento)
if __name__ == "__main__":
    main()
