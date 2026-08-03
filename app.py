import logging
import os
import threading
import time
from datetime import date, datetime

import django

import pandas as pd
import requests
import streamlit as st

# Configuração da página (DEVE SER A PRIMEIRA COISA NO SCRIPT)
st.set_page_config(
    page_title="SGR", page_icon="📊", layout="wide", initial_sidebar_state="expanded"
)

# Configurações para prevenir hibernação
if "session_started" not in st.session_state:
    st.session_state["session_started"] = True
    st.session_state["last_activity"] = time.time()

# Auto-refresh para manter sessão ativa
if time.time() - st.session_state.get("last_activity", 0) > 240:  # 4 minutos
    st.session_state["last_activity"] = time.time()
    st.rerun()

# Injetar credenciais do Streamlit Secrets no os.environ para o Django
# (só relevante no Streamlit Community Cloud — no deploy Docker/local as
# credenciais já vêm do .env/env_file. load_if_toml_exists() checa a existência
# do secrets.toml sem imprimir o aviso "No secrets found": o Streamlit chama
# st.error() internamente antes de levantar a exceção que o try/except pegaria,
# então só o guard evita o aviso visual — o try/except sozinho não bastava)
if not os.environ.get("SGR_DOCKER_DEPLOY") and st.secrets.load_if_toml_exists():
    try:
        if "database" in st.secrets:
            for _key in ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"]:
                if _key in st.secrets["database"]:
                    os.environ[_key] = str(st.secrets["database"][_key])
    except Exception:
        pass  # Em ambiente local, usa variáveis já definidas no ambiente

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
django.setup()

from apps.auth.modules import menu
from apps.auth.views import login_screen
from apps.boletos.views import main as boletos_main
from apps.clientes.views import main as clientes_main
from apps.comex.views import main as comex_main
from apps.estoque.views import main as estoque_main
from apps.extratos.views import main as extratos_main
from apps.sac.views import main as sac_main
from apps.vendas.pedidos import main as pedidos_main
from apps.vendas.recebimentos import main as recebimentos_main
from apps.vendas.views import main as vendas_main

# Importações após a configuração da página
from service import DataService as AppDataService
from service import UserService

# Importações da aplicação de vendas refatorada
try:
    from core.container_vendas import DIContainer
    from core.exceptions import BusinessLogicError, SGRException, ValidationError
    from domain.services.vendas_service import VendasService
    from presentation.components.data_grid_simple import DataGrid
    from presentation.components.forms_vendas import (
        FilterForm,
        LoadingHelper,
        MetricsDisplay,
        ValidationHelper,
    )
    from presentation.styles.theme_simple import apply_theme

    VENDAS_REFATORADO_AVAILABLE = True
except ImportError as e:
    VENDAS_REFATORADO_AVAILABLE = False

# Instanciar DataService e UserService
data_service = (
    AppDataService()
)  # Renomeado para evitar conflito com o DataService de vendas
user_service = UserService(data_service)

# Instanciar serviços de vendas
if VENDAS_REFATORADO_AVAILABLE:
    container = DIContainer()
    vendas_service = container.get_vendas_service()
    logger = logging.getLogger(__name__)


# Função para fazer requisições periódicas (keep-alive) - REMOVIDO PROBLEMA DE SCRIPT CONTEXT
def keep_alive():
    """
    Keep-alive em background sem problemas de ScriptRunContext
    Usa apenas requests, sem interação com Streamlit
    """
    import logging
    import time

    import requests

    # Configurar logger específico para keep-alive
    keep_alive_logger = logging.getLogger("keep_alive")
    keep_alive_logger.setLevel(logging.INFO)

    while True:
        try:
            # Fazer requisição silenciosa apenas para manter vivo
            # Não usar st.write aqui para evitar ScriptRunContext warnings
            response = requests.get("https://oficialsport.streamlit.app/", timeout=10)
            keep_alive_logger.info(
                f"Keep-alive enviado - Status: {response.status_code}"
            )
        except Exception as e:
            keep_alive_logger.warning(f"Erro no keep-alive: {e}")
        time.sleep(300)  # 5 minutos


# Verificar se deve inicializar keep-alive (apenas uma vez por sessão)
if "keep_alive_started" not in st.session_state:
    thread = threading.Thread(target=keep_alive, daemon=True)
    thread.start()
    st.session_state["keep_alive_started"] = True


def _show_manual_dialog():
    """
    Exibe o manual em uma janela de diálogo
    """
    try:
        # Ler o conteúdo do manual
        manual_path = "documentacao/Manual_Relatorio_Vendas.md"

        with open(manual_path, "r", encoding="utf-8") as file:
            markdown_content = file.read()

        # Usar st.expander para simular uma janela separada
        with st.expander("📖 Manual do Relatório de Vendas", expanded=True):
            # Converter markdown para HTML com melhor formatação
            html_content = _convert_markdown_to_html(markdown_content)
            st.markdown(html_content, unsafe_allow_html=True)

            # Adicionar botão para fechar
            if st.button("❌ Fechar Manual"):
                st.rerun()

    except FileNotFoundError:
        st.error("❌ Manual não encontrado. Verifique se o arquivo existe.")
    except Exception as e:
        st.error(f"❌ Erro ao carregar o manual: {str(e)}")


def _convert_markdown_to_html(markdown_content):
    """
    Converte markdown para HTML com melhor formatação para Streamlit
    """
    # Importar biblioteca markdown se disponível, senão usar formatação básica
    try:
        import markdown

        html = markdown.markdown(markdown_content, extensions=["tables", "fenced_code"])
        return f"""
        <div style="
            font-family: 'Roboto', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-height: 600px;
            overflow-y: auto;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 10px;
            border: 1px solid #e9ecef;
        ">
            {html}
        </div>
        """
    except ImportError:
        # Se não tiver markdown, usar formatação básica
        return _basic_markdown_to_html(markdown_content)


def _basic_markdown_to_html(content):
    """
    Conversão básica de markdown para HTML
    """
    # Substituições básicas para formatação
    content = content.replace("\n# ", "\n<h1>")
    content = content.replace("\n## ", "\n<h2>")
    content = content.replace("\n### ", "\n<h3>")
    content = content.replace("\n#### ", "\n<h4>")
    content = content.replace("\n", "<br>")
    content = content.replace("**", "<strong>").replace("**", "</strong>")
    content = content.replace("*", "<em>").replace("*", "</em>")
    content = content.replace("`", "<code>").replace("`", "</code>")

    return f"""
    <div style="
        font-family: 'Roboto', Arial, sans-serif;
        line-height: 1.6;
        color: #333;
        max-height: 600px;
        overflow-y: auto;
        padding: 20px;
        background-color: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #e9ecef;
    ">
        {content}
    </div>
    """


def vendas_dashboard():
    """
    Dashboard de vendas integrado

    NOTA: Esta função é código legado e não é mais utilizada.
    O módulo de vendas agora usa apps/vendas/views.py (vendas_main)
    """
    try:
        # Verificar se está no modo manual
        if st.session_state.get("view_mode") == "manual":
            _render_manual_fullscreen()
            return

        # Aplicar tema
        apply_theme()

        # Header
        st.markdown(
            "<h1 style='text-align: center; color: #1E88E5;'>📊 SGR - Dashboard de Vendas Geral</h1>",
            unsafe_allow_html=True,
        )

        # Botão Ler Manual centralizado abaixo do título
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            # Botão do manual - navegar para tela cheia
            if st.button("📖 Ler Manual", type="secondary", use_container_width=True):
                st.session_state["view_mode"] = "manual"
                st.rerun()

        st.markdown("---")

        # Renderizar seções
        _render_update_info()
        _render_filters_and_metrics()
        _render_download_section()
        _render_charts()
        _render_data_grid()
        _render_produtos_detalhados()

    except SGRException as e:
        logger.error(f"SGR Error: {str(e)}")
        st.error(f"Erro na aplicação: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        st.error("Erro inesperado na aplicação. Verifique os logs.")


def _render_update_info():
    """Renderiza informações de atualização"""
    st.subheader("🔄 Informações de Atualização")

    try:
        info = vendas_service.get_informacoes_atualizacao()

        with st.expander("Dados da Última Sincronização", expanded=True):
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.markdown(
                    f"""
                <div style='
                    background: #ffffff; 
                    border-radius: 10px; 
                    padding: 16px; 
                    text-align: center; 
                    box-shadow: 0 4px 12px rgba(30, 136, 229, 0.15);
                    font-family: Roboto, sans-serif;
                '>
                    <div style='font-size: 0.9rem; color: #1E88E5; margin-bottom: 8px; font-weight: 600;'>📅 Data</div>
                    <div style='font-size: 1.4rem; font-weight: 700; color: #1E88E5;'>{info['data']}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col2:
                st.markdown(
                    f"""
                <div style='
                    background: #ffffff; 
                    border-radius: 10px; 
                    padding: 16px; 
                    text-align: center; 
                    box-shadow: 0 4px 12px rgba(30, 136, 229, 0.15);
                    font-family: Roboto, sans-serif;
                '>
                    <div style='font-size: 0.9rem; color: #1E88E5; margin-bottom: 8px; font-weight: 600;'>⏰ Hora</div>
                    <div style='font-size: 1.4rem; font-weight: 700; color: #1E88E5;'>{info['hora']}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col3:
                st.markdown(
                    f"""
                <div style='
                    background: #ffffff; 
                    border-radius: 10px; 
                    padding: 16px; 
                    text-align: center; 
                    box-shadow: 0 4px 12px rgba(30, 136, 229, 0.15);
                    font-family: Roboto, sans-serif;
                    min-height: 90px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                '>
                    <div style='font-size: 0.8rem; color: #1E88E5; margin-bottom: 8px; font-weight: 600;'>📊 Período</div>
                    <div style='font-size: 1.1rem; font-weight: 700; color: #1E88E5;'>{info['periodo']}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col4:
                st.markdown(
                    f"""
                <div style='
                    background: #ffffff; 
                    border-radius: 10px; 
                    padding: 16px; 
                    text-align: center; 
                    box-shadow: 0 4px 12px rgba(30, 136, 229, 0.15);
                    font-family: Roboto, sans-serif;
                '>
                    <div style='font-size: 0.9rem; color: #1E88E5; margin-bottom: 8px; font-weight: 600;'>✅ Inseridos</div>
                    <div style='font-size: 1.4rem; font-weight: 700; color: #1E88E5;'>{info['inseridos']}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col5:
                st.markdown(
                    f"""
                <div style='
                    background: #ffffff; 
                    border-radius: 10px; 
                    padding: 16px; 
                    text-align: center; 
                    box-shadow: 0 4px 12px rgba(30, 136, 229, 0.15);
                    font-family: Roboto, sans-serif;
                '>
                    <div style='font-size: 0.9rem; color: #1E88E5; margin-bottom: 8px; font-weight: 600;'>🔄 Atualizados</div>
                    <div style='font-size: 1.4rem; font-weight: 700; color: #1E88E5;'>{info['atualizados']}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    except Exception as e:
        logger.warning(f"Could not load update info: {str(e)}")
        st.warning("Informações de atualização indisponíveis")


def _render_metrics_cards(metrics):
    """Renderiza métricas em cards no mesmo estilo das Informações de Atualização"""
    if not metrics:
        st.info("Nenhuma métrica disponível")
        return

    # Função auxiliar para formatar moeda
    def format_currency(value):
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # Primeira linha: Total Entradas, Total Parcelado, Valor Total
    col1, col2, col3 = st.columns(3)

    with col1:
        entradas = metrics.get("total_entradas", 0)
        valor_formatado = format_currency(entradas)
        st.markdown(
            f"""
        <div style='
            background: #ffffff;
            border-radius: 10px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(30, 136, 229, 0.15);
            font-family: Roboto, sans-serif;
            min-height: 90px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        '>
            <div style='font-size: 0.9rem; color: #1E88E5; margin-bottom: 8px; font-weight: 600;'>💰 Total Entradas</div>
            <div style='font-size: 1.2rem; font-weight: 700; color: #1E88E5;'>{valor_formatado}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        parcelado = metrics.get("total_parcelado", 0)
        parcelado_formatado = format_currency(parcelado)
        st.markdown(
            f"""
        <div style='
            background: #ffffff;
            border-radius: 10px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(30, 136, 229, 0.15);
            font-family: Roboto, sans-serif;
            min-height: 90px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        '>
            <div style='font-size: 0.9rem; color: #1E88E5; margin-bottom: 8px; font-weight: 600;'>⏳ Total Parcelado</div>
            <div style='font-size: 1.2rem; font-weight: 700; color: #1E88E5;'>{parcelado_formatado}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        total_valor = metrics.get("total_valor", 0)
        total_formatado = format_currency(total_valor)
        st.markdown(
            f"""
        <div style='
            background: #ffffff;
            border-radius: 10px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(30, 136, 229, 0.15);
            font-family: Roboto, sans-serif;
            min-height: 90px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        '>
            <div style='font-size: 0.9rem; color: #1E88E5; margin-bottom: 8px; font-weight: 600;'>💎 Valor Total</div>
            <div style='font-size: 1.2rem; font-weight: 700; color: #1E88E5;'>{total_formatado}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Segunda linha: Total de Vendas, Ticket Médio, Margem Média
    col4, col5, col6 = st.columns(3)

    with col4:
        total_quantidade = metrics.get("total_quantidade", 0)
        quantidade_formatada = f"{int(total_quantidade):,}".replace(",", ".")
        st.markdown(
            f"""
        <div style='
            background: #ffffff;
            border-radius: 10px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(30, 136, 229, 0.15);
            font-family: Roboto, sans-serif;
            min-height: 90px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        '>
            <div style='font-size: 0.9rem; color: #1E88E5; margin-bottom: 8px; font-weight: 600;'>📊 Total de Vendas</div>
            <div style='font-size: 1.2rem; font-weight: 700; color: #1E88E5;'>{quantidade_formatada}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col5:
        ticket_medio = metrics.get("ticket_medio", 0)
        ticket_formatado = format_currency(ticket_medio)
        st.markdown(
            f"""
        <div style='
            background: #ffffff;
            border-radius: 10px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(30, 136, 229, 0.15);
            font-family: Roboto, sans-serif;
            min-height: 90px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        '>
            <div style='font-size: 0.9rem; color: #1E88E5; margin-bottom: 8px; font-weight: 600;'>🎯 Ticket Médio</div>
            <div style='font-size: 1.2rem; font-weight: 700; color: #1E88E5;'>{ticket_formatado}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col6:
        margem_media = metrics.get("margem_media", 0)
        margem_texto = f"{margem_media:.1f}%" if margem_media > 0 else "N/A"
        st.markdown(
            f"""
        <div style='
            background: #ffffff;
            border-radius: 10px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(30, 136, 229, 0.15);
            font-family: Roboto, sans-serif;
            min-height: 90px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        '>
            <div style='font-size: 0.9rem; color: #1E88E5; margin-bottom: 8px; font-weight: 600;'>📈 Margem Média</div>
            <div style='font-size: 1.2rem; font-weight: 700; color: #1E88E5;'>{margem_texto}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )


def _render_metrics_produtos():
    """Renderiza métricas de produtos (Equipamentos vs Acessórios) em cards - baseado em valor proporcional"""
    try:
        # Verificar se há dados de vendas
        if "df_vendas" not in st.session_state or st.session_state["df_vendas"] is None:
            return

        df_vendas = st.session_state["df_vendas"]
        if df_vendas.empty:
            return

        # Obter IDs das vendas filtradas
        if "ID_Gestao" not in df_vendas.columns:
            logger.warning("Campo ID_Gestao não encontrado no dataframe de vendas")
            return

        venda_ids = df_vendas["ID_Gestao"].tolist()

        # Buscar produtos detalhados (para calcular proporção por venda)
        df_produtos = vendas_service.get_produtos_detalhados(venda_ids=venda_ids)

        if df_produtos.empty or "NomeGrupo" not in df_produtos.columns:
            logger.warning(
                "Colunas necessárias não encontradas no dataframe de produtos"
            )
            return

        # Verificar se há campo Venda_ID para fazer o join
        if "Venda_ID" not in df_produtos.columns:
            logger.warning("Campo Venda_ID não encontrado no dataframe de produtos")
            return

        # Criar dicionário com ValorTotal de cada venda
        vendas_dict = df_vendas.set_index("ID_Gestao")["ValorTotal"].to_dict()

        # Classificar produtos por tipo
        grupos_acessorios = ["PEÇA DE REPOSIÇÃO", "ACESSÓRIOS"]
        df_produtos["Tipo"] = df_produtos["NomeGrupo"].apply(
            lambda x: "Acessório" if x and x in grupos_acessorios else "Equipamento"
        )

        # Garantir que ValorTotal seja numérico
        df_produtos["ValorTotal"] = pd.to_numeric(
            df_produtos["ValorTotal"], errors="coerce"
        ).fillna(0)

        # Para cada produto, calcular sua proporção dentro da venda e aplicar ao ValorTotal da venda
        def calcular_valor_proporcional(row):
            """Calcula valor proporcional do produto baseado no ValorTotal da venda"""
            venda_id = row["Venda_ID"]
            valor_produto = row["ValorTotal"]

            # Obter ValorTotal da venda
            valor_venda = vendas_dict.get(venda_id, 0)

            if valor_venda == 0:
                return 0

            # Calcular soma de produtos desta venda
            produtos_venda = df_produtos[df_produtos["Venda_ID"] == venda_id]
            soma_produtos = produtos_venda["ValorTotal"].sum()

            if soma_produtos == 0:
                return 0

            # Calcular proporção e aplicar ao valor real da venda
            proporcao = valor_produto / soma_produtos
            valor_proporcional = valor_venda * proporcao

            return valor_proporcional

        # Aplicar cálculo proporcional
        df_produtos["ValorProporcional"] = df_produtos.apply(
            calcular_valor_proporcional, axis=1
        )

        # Calcular totais por tipo usando valores proporcionais
        valor_equipamentos = df_produtos[df_produtos["Tipo"] == "Equipamento"][
            "ValorProporcional"
        ].sum()
        valor_acessorios = df_produtos[df_produtos["Tipo"] == "Acessório"][
            "ValorProporcional"
        ].sum()
        valor_total = valor_equipamentos + valor_acessorios

        # Evitar divisão por zero
        if valor_total == 0:
            return

        # Calcular percentuais
        perc_equipamentos = (
            (valor_equipamentos / valor_total * 100) if valor_total > 0 else 0
        )
        perc_acessorios = (
            (valor_acessorios / valor_total * 100) if valor_total > 0 else 0
        )

        # Formatar valores monetários (padrão brasileiro)
        valor_equipamentos_fmt = (
            f"R$ {valor_equipamentos:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        valor_acessorios_fmt = (
            f"R$ {valor_acessorios:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        # Renderizar título
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style='text-align: center; margin-bottom: 15px;'>
                <h4 style='color: #1E88E5; font-family: Roboto, sans-serif; margin: 0;'>
                    📦 Métrica de Produtos
                </h4>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Renderizar cards
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f"""
            <div style='
                background: #ffffff;
                border-radius: 10px;
                padding: 16px;
                text-align: center;
                box-shadow: 0 4px 12px rgba(30, 136, 229, 0.15);
                font-family: Roboto, sans-serif;
                min-height: 90px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            '>
                <div style='font-size: 0.9rem; color: #1E88E5; margin-bottom: 8px; font-weight: 600;'>🏋️ Equipamentos</div>
                <div style='font-size: 1.2rem; font-weight: 700; color: #1E88E5;'>{perc_equipamentos:.1f}%</div>
                <div style='font-size: 1.2rem; color: #6b7280; margin-top: 4px;'>{valor_equipamentos_fmt}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"""
            <div style='
                background: #ffffff;
                border-radius: 10px;
                padding: 16px;
                text-align: center;
                box-shadow: 0 4px 12px rgba(30, 136, 229, 0.15);
                font-family: Roboto, sans-serif;
                min-height: 90px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            '>
                <div style='font-size: 0.9rem; color: #1E88E5; margin-bottom: 8px; font-weight: 600;'>🔧 Acessórios</div>
                <div style='font-size: 1.2rem; font-weight: 700; color: #1E88E5;'>{perc_acessorios:.1f}%</div>
                <div style='font-size: 1.2rem; color: #6b7280; margin-top: 4px;'>{valor_acessorios_fmt}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    except Exception as e:
        logger.error(f"Erro ao renderizar métricas de produtos: {str(e)}")
        # Não exibir erro para o usuário, apenas não mostrar as métricas


def _render_gauge_meta():
    """Renderiza gauge de meta de vendas do mês atual - Estilo circular com tons de azul"""
    try:
        import plotly.graph_objects as go

        # Obter meta configurada
        meta = vendas_service.get_meta_vendas()

        if not meta or meta <= 0:
            # Meta não configurada, não exibir gauge
            return

        # Obter vendas do mês atual (sempre, independente dos filtros aplicados)
        hoje = datetime.now()
        data_inicial = datetime(hoje.year, hoje.month, 1).date()
        data_final = hoje.date()

        df_mes_atual = vendas_service.venda_repository.get_vendas_filtradas(
            data_inicial=data_inicial,
            data_final=data_final,
            situacoes_excluir=[
                'Cancelada (sem financeiro)',
                'Não considerar - Excluidos',
            ],
        )

        # Processar dados
        df_mes_atual = vendas_service._processar_dados_vendas(df_mes_atual)

        # Calcular valor total do mês
        valor_total_mes = (
            df_mes_atual["ValorTotal"].sum() if not df_mes_atual.empty else 0
        )

        # Calcular percentual atingido
        percentual = (valor_total_mes / meta * 100) if meta > 0 else 0

        # Determinar tonalidade de azul baseada no percentual
        if percentual >= 100:
            cor_gauge = "#0d47a1"  # Azul escuro (meta atingida)
        elif percentual >= 75:
            cor_gauge = "#1976d2"  # Azul médio
        elif percentual >= 50:
            cor_gauge = "#42a5f5"  # Azul claro
        else:
            cor_gauge = "#90caf9"  # Azul muito claro

        # Renderizar gauge
        st.markdown("<br>", unsafe_allow_html=True)

        # Formatar valores para exibição
        valor_realizado_fmt = (
            f"R$ {valor_total_mes:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        valor_meta_fmt = (
            f"R$ {meta:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

        # Criar gauge circular estilo donut usando Plotly
        # Percentual restante para completar 100%
        percentual_restante = max(0, 100 - percentual)

        fig = go.Figure(
            data=[
                go.Pie(
                    values=[percentual, percentual_restante],
                    labels=["Atingido", "Restante"],
                    hole=0.7,  # Tamanho do buraco central (donut)
                    marker=dict(
                        colors=[
                            cor_gauge,
                            "#e0e0e0",
                        ],  # Azul para atingido, cinza claro para restante
                        line=dict(color="#ffffff", width=3),
                    ),
                    textinfo="none",  # Não mostrar texto nas fatias
                    hoverinfo="label+percent",
                    showlegend=False,
                )
            ]
        )

        # Adicionar anotação no centro com o percentual
        fig.add_annotation(
            text=f"<b>{percentual:.0f}%</b>",
            x=0.5,
            y=0.55,
            font=dict(size=48, color=cor_gauge, family="Roboto"),
            showarrow=False,
            xref="paper",
            yref="paper",
        )

        # Adicionar texto "da Meta" abaixo do percentual
        fig.add_annotation(
            text="da Meta",
            x=0.5,
            y=0.42,
            font=dict(size=16, color="#6b7280", family="Roboto"),
            showarrow=False,
            xref="paper",
            yref="paper",
        )

        fig.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        # Layout com título e gauge
        st.markdown(
            """
            <div style='text-align: center; margin-bottom: 10px;'>
                <h3 style='color: #1E88E5; font-family: Roboto, sans-serif; margin: 0;'>
                    🎯 Meta de Vendas do Mês
                </h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Exibir gauge centralizado
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Card com fundo branco para o gauge
            st.markdown(
                """
                <div style='
                    background: #ffffff;
                    border-radius: 15px;
                    padding: 20px;
                    box-shadow: 0 6px 16px rgba(30, 136, 229, 0.2);
                    margin-bottom: 15px;
                '>
                """,
                unsafe_allow_html=True,
            )

            st.plotly_chart(fig, use_container_width=True, key="gauge_meta_vendas")

            st.markdown("</div>", unsafe_allow_html=True)

            # Informações adicionais abaixo do gauge
            st.markdown(
                f"""
                <div style='
                    background: #ffffff;
                    border-radius: 10px;
                    padding: 20px;
                    text-align: center;
                    box-shadow: 0 4px 12px rgba(30, 136, 229, 0.15);
                '>
                    <div style='margin-bottom: 15px;'>
                        <div style='font-size: 0.9rem; color: #6b7280; margin-bottom: 5px; font-weight: 500;'>💰 Realizado no Mês</div>
                        <div style='font-size: 1.5rem; font-weight: 700; color: {cor_gauge};'>{valor_realizado_fmt}</div>
                    </div>
                    <div style='border-top: 1px solid #e5e7eb; padding-top: 15px;'>
                        <div style='font-size: 0.9rem; color: #6b7280; margin-bottom: 5px; font-weight: 500;'>🎯 Meta do Mês</div>
                        <div style='font-size: 1.3rem; font-weight: 600; color: #1E88E5;'>{valor_meta_fmt}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    except Exception as e:
        logger.error(f"Erro ao renderizar gauge de meta: {str(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        # Não exibir erro para o usuário, apenas não mostrar o gauge


def _calcular_vendas_periodo_anterior(data_inicio, data_fim, vendedores_nomes):
    """
    Calcula as vendas de cada vendedor no mesmo período do ano anterior

    Args:
        data_inicio: Data inicial do período atual
        data_fim: Data final do período atual
        vendedores_nomes: Lista de nomes dos vendedores

    Returns:
        dict: Dicionário com vendas do período anterior por vendedor
    """
    try:
        from datetime import timedelta

        from dateutil.relativedelta import relativedelta

        # Calcular período anterior (mesmo período do ano anterior)
        data_inicio_anterior = data_inicio - relativedelta(years=1)
        data_fim_anterior = data_fim - relativedelta(years=1)

        # Buscar vendas do período anterior
        df_periodo_anterior = vendas_service.venda_repository.get_vendas_filtradas(
            data_inicial=data_inicio_anterior,
            data_final=data_fim_anterior,
        )

        if df_periodo_anterior.empty:
            return {}

        # Processar dados
        df_periodo_anterior = vendas_service._processar_dados_vendas(
            df_periodo_anterior
        )

        # Agrupar por vendedor
        vendas_anteriores = {}
        if (
            not df_periodo_anterior.empty
            and "VendedorNome" in df_periodo_anterior.columns
        ):
            df_agrupado = (
                df_periodo_anterior.groupby("VendedorNome")["ValorTotal"]
                .sum()
                .reset_index()
            )
            for _, row in df_agrupado.iterrows():
                vendas_anteriores[row["VendedorNome"]] = float(row["ValorTotal"])

        return vendas_anteriores

    except Exception as e:
        logger.error(f"Erro ao calcular vendas do período anterior: {str(e)}")
        return {}


def _calcular_vendas_mes_atual_para_gauge(vendedores_nomes):
    """
    Calcula as vendas do mês atual (sempre) para os gauges

    Realizado: 01 do mês atual até hoje
    Meta: 01 do mesmo mês do ano anterior até o mesmo dia

    Args:
        vendedores_nomes: Lista de nomes dos vendedores

    Returns:
        tuple: (dict realizado, dict meta) com vendas por vendedor
    """
    try:
        from datetime import datetime

        from dateutil.relativedelta import relativedelta

        # Sempre usar mês atual
        hoje = datetime.now()
        data_inicio_atual = datetime(hoje.year, hoje.month, 1).date()
        data_fim_atual = hoje.date()

        # Calcular mesmo período do ano anterior
        data_inicio_anterior = data_inicio_atual - relativedelta(years=1)
        data_fim_anterior = data_fim_atual - relativedelta(years=1)

        # Buscar vendas do período atual (realizado)
        df_periodo_atual = vendas_service.venda_repository.get_vendas_filtradas(
            data_inicial=data_inicio_atual,
            data_final=data_fim_atual,
        )

        # Buscar vendas do período anterior (meta)
        df_periodo_anterior = vendas_service.venda_repository.get_vendas_filtradas(
            data_inicial=data_inicio_anterior,
            data_final=data_fim_anterior,
        )

        # Processar realizado
        vendas_realizadas = {}
        if not df_periodo_atual.empty:
            df_periodo_atual = vendas_service._processar_dados_vendas(df_periodo_atual)
            if "VendedorNome" in df_periodo_atual.columns:
                df_agrupado = (
                    df_periodo_atual.groupby("VendedorNome")["ValorTotal"]
                    .sum()
                    .reset_index()
                )
                for _, row in df_agrupado.iterrows():
                    vendas_realizadas[row["VendedorNome"]] = float(row["ValorTotal"])

        # Processar meta (período anterior)
        vendas_meta = {}
        if not df_periodo_anterior.empty:
            df_periodo_anterior = vendas_service._processar_dados_vendas(
                df_periodo_anterior
            )
            if "VendedorNome" in df_periodo_anterior.columns:
                df_agrupado = (
                    df_periodo_anterior.groupby("VendedorNome")["ValorTotal"]
                    .sum()
                    .reset_index()
                )
                for _, row in df_agrupado.iterrows():
                    vendas_meta[row["VendedorNome"]] = float(row["ValorTotal"])

        return vendas_realizadas, vendas_meta

    except Exception as e:
        logger.error(f"Erro ao calcular vendas do mês atual para gauge: {str(e)}")
        return {}, {}


def _render_vendedores_com_fotos(vendas_por_vendedor):
    """Renderiza todos os vendedores da tabela com suas fotos em cards 6x2"""
    import base64
    import os
    from io import BytesIO

    import pandas as pd
    from PIL import Image

    # Lista completa de vendedores da tabela Vendedores (ordem das fotos)
    vendedores_tabela = [
        {"nome": "Noé Dutra", "foto": "1"},
        {"nome": "Nilton Jonas Gonçalves de Moraes", "foto": "2"},
        {"nome": "César Henrique Rodrigues", "foto": "3"},
        {"nome": "Rocha Jr.", "foto": "4"},
        {"nome": "Diney Scalabrini", "foto": "5"},
        {"nome": "João Paulo", "foto": "6"},
        {"nome": "Lauro Jarbas de Oliveira", "foto": "7"},
        {"nome": "Giovana Lelis", "foto": "8"},
        {"nome": "Carlos Gabriel Carvalho Macedo", "foto": "9"},
        {"nome": "Cássio Gadagnoto", "foto": "10"},
        {"nome": "André Souza", "foto": "11"},
        {"nome": "João Victor", "foto": "12"},
    ]

    # Buscar nomes curtos e percentuais do banco de dados
    dados_vendedores = vendas_service.venda_repository.get_vendedores_com_nome_curto()

    # Obter datas do filtro aplicado (ou calcular mês atual)
    from dateutil.relativedelta import relativedelta

    data_inicio = st.session_state.get("data_inicio_filtro")
    data_fim = st.session_state.get("data_fim_filtro")

    if not data_inicio or not data_fim:
        hoje = datetime.now()
        data_inicio = datetime(hoje.year, hoje.month, 1).date()
        data_fim = hoje.date()

    # Calcular ano anterior para exibição
    ano_anterior = (data_inicio - relativedelta(years=1)).year

    # Calcular vendas do mesmo período no ano anterior
    vendedores_nomes = [v["nome"] for v in vendedores_tabela]
    vendas_anteriores = _calcular_vendas_periodo_anterior(
        data_inicio, data_fim, vendedores_nomes
    )

    # Criar dicionário de vendas de TODOS os vendedores (sem limite top_n)
    # Usa df_vendas completo da session_state para não perder vendedores fora do top 10
    vendas_dict = {}
    df_vendas_completo = st.session_state.get("df_vendas", pd.DataFrame())

    if (
        df_vendas_completo is not None
        and not df_vendas_completo.empty
        and "VendedorNome" in df_vendas_completo.columns
        and "ValorTotal" in df_vendas_completo.columns
    ):
        df_agrupado = (
            df_vendas_completo.groupby("VendedorNome")["ValorTotal"].sum().reset_index()
        )
        for _, row in df_agrupado.iterrows():
            vendas_dict[row["VendedorNome"]] = {
                "total_valor": float(row["ValorTotal"]),
            }
    elif vendas_por_vendedor is not None and not vendas_por_vendedor.empty:
        # Fallback: usar vendas_por_vendedor se df_vendas não estiver disponível
        for _, row in vendas_por_vendedor.iterrows():
            vendas_dict[row["VendedorNome"]] = {
                "total_valor": float(row["total_valor"]),
            }

    # Preparar dados completos dos vendedores
    vendedores_completos = []
    for vendedor in vendedores_tabela:
        nome = vendedor["nome"]
        dados_vend = dados_vendedores.get(nome, {})
        nome_curto = dados_vend.get("curto", nome)
        percentual_meta = dados_vend.get("percentual", 0.0)
        vendas_ant = vendas_anteriores.get(nome, 0.0)

        total_valor = vendas_dict[nome]["total_valor"] if nome in vendas_dict else 0.0

        vendedores_completos.append(
            {
                "nome": nome,
                "nome_curto": nome_curto,
                "foto": vendedor["foto"],
                "total_valor": total_valor,
                "vendas_ano_anterior": vendas_ant,
                "percentual_meta": percentual_meta,
                "ano_anterior": ano_anterior,
            }
        )

    # Ordenar vendedores por volume de vendas (maior para menor)
    vendedores_ordenados = sorted(
        vendedores_completos, key=lambda x: x["total_valor"], reverse=True
    )

    # Função para converter imagem em base64 mantendo transparência
    def get_image_base64(image_path, size=(80, 80)):
        try:
            if os.path.exists(image_path):
                img = Image.open(image_path)

                # Manter transparência se for PNG
                if img.mode in ("RGBA", "LA") or (
                    img.mode == "P" and "transparency" in img.info
                ):
                    # Para PNG com transparência, manter o canal alfa
                    img = img.convert("RGBA")
                    img.thumbnail(size, Image.Resampling.LANCZOS)
                    buffered = BytesIO()
                    img.save(buffered, format="PNG")
                else:
                    # Para outros formatos, converter para RGB
                    img = img.convert("RGB")
                    img.thumbnail(size, Image.Resampling.LANCZOS)
                    buffered = BytesIO()
                    img.save(buffered, format="PNG")

                img_str = base64.b64encode(buffered.getvalue()).decode()
                return f"data:image/png;base64,{img_str}"
            else:
                return None
        except Exception as e:
            return None

    # Função para formatar moeda
    def format_currency(value):
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # Renderizar cards dos vendedores em layout 6x2 (6 por linha, 2 linhas)
    # Primeira linha (vendedores 1-6)
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    cols_linha1 = [col1, col2, col3, col4, col5, col6]

    for i in range(6):  # Primeira linha
        if i < len(vendedores_ordenados):
            vendedor = vendedores_ordenados[i]
            _render_card_vendedor(
                cols_linha1[i], vendedor, get_image_base64, format_currency
            )

    # Segunda linha (vendedores 7-12)
    col7, col8, col9, col10, col11, col12 = st.columns(6)
    cols_linha2 = [col7, col8, col9, col10, col11, col12]

    for i in range(6):  # Segunda linha
        idx = i + 6
        if idx < len(vendedores_ordenados):
            vendedor = vendedores_ordenados[idx]
            _render_card_vendedor(
                cols_linha2[i], vendedor, get_image_base64, format_currency
            )


def _criar_gauge_vendedor(meta, realizado):
    """
    Cria um gauge pequeno para o vendedor

    Args:
        meta: Valor da meta (período anterior)
        realizado: Valor realizado (período atual)

    Returns:
        str: HTML do gauge em formato base64
    """
    try:
        import base64

        import plotly.graph_objects as go

        # Calcular percentual
        percentual = (realizado / meta * 100) if meta > 0 else 0

        # Determinar cor baseada no percentual
        if percentual >= 100:
            cor_gauge = "#0d47a1"  # Azul escuro
        elif percentual >= 75:
            cor_gauge = "#1976d2"  # Azul médio
        elif percentual >= 50:
            cor_gauge = "#42a5f5"  # Azul claro
        else:
            cor_gauge = "#90caf9"  # Azul muito claro

        # Percentual restante
        percentual_restante = max(0, 100 - percentual)

        # Criar gauge estilo donut
        fig = go.Figure(
            data=[
                go.Pie(
                    values=[percentual, percentual_restante],
                    labels=["Atingido", "Restante"],
                    hole=0.65,
                    marker=dict(
                        colors=[cor_gauge, "#e0e0e0"],
                        line=dict(color="#ffffff", width=1),
                    ),
                    textinfo="none",
                    hoverinfo="label+percent",
                    showlegend=False,
                )
            ]
        )

        # Adicionar percentual no centro
        fig.add_annotation(
            text=f"<b>{percentual:.0f}%</b>",
            x=0.5,
            y=0.5,
            font=dict(size=12, color=cor_gauge, family="Roboto"),
            showarrow=False,
            xref="paper",
            yref="paper",
        )

        fig.update_layout(
            height=60,
            width=60,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        # Converter para imagem base64
        try:
            img_bytes = fig.to_image(format="png", width=60, height=60)
            img_b64 = base64.b64encode(img_bytes).decode()
            return f"data:image/png;base64,{img_b64}"
        except Exception:
            return None

    except Exception as e:
        logger.error(f"Erro ao criar gauge do vendedor: {str(e)}")
        return None


def _render_card_vendedor(col, vendedor, get_image_base64, format_currency):
    """Renderiza um card individual do vendedor com novo layout"""
    with col:
        # Buscar foto do vendedor
        foto_path_jpg = f"fotos/{vendedor['foto']}.jpg"
        foto_path_png = f"fotos/{vendedor['foto']}.png"

        # Usar JPG se existir, senão PNG
        foto_path = foto_path_jpg if os.path.exists(foto_path_jpg) else foto_path_png
        image_b64 = get_image_base64(foto_path)

        # Calcular percentual: vendas atuais / (vendas ano anterior + percentual crescimento)
        vendas_ant = vendedor.get("vendas_ano_anterior", 0.0)
        percentual_meta = vendedor.get("percentual_meta", 0.0)
        # Meta = vendas_ano_anterior * (1 + Percentual/100)
        meta = vendas_ant * (1 + percentual_meta / 100) if vendas_ant > 0 else 0
        percentual = (vendedor["total_valor"] / meta * 100) if meta > 0 else 0
        ano_anterior = vendedor.get("ano_anterior", "")

        # Foto ou avatar com iniciais
        if image_b64:
            foto_html = f'<img src="{image_b64}" style="width: 80px; height: 80px; border-radius: 50%; display: block; margin: 0 auto 12px auto; object-fit: cover; border: 3px solid #1E88E5;">'
        else:
            iniciais = "".join(
                [nome[0] for nome in vendedor["nome"].split()[:2]]
            ).upper()
            foto_html = f"""<div style="
                width: 80px;
                height: 80px;
                border-radius: 50%;
                background: linear-gradient(135deg, #1E88E5, #1565C0);
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                font-weight: 700;
                margin: 0 auto 12px auto;
                border: 3px solid #1E88E5;
            ">{iniciais}</div>"""

        st.markdown(
            f"""
        <div style='
            background: #ffffff;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 6px 16px rgba(30, 136, 229, 0.2);
            font-family: Roboto, sans-serif;
            margin-bottom: 20px;
            border: 2px solid #E3F2FD;
        '>
            {foto_html}
            <div style='font-size: 0.95rem; color: #1E88E5; font-weight: 600; margin-bottom: 8px;'>
                {vendedor.get('nome_curto', vendedor['nome'])}
            </div>
            <div style='font-size: 1.2rem; font-weight: 700; color: #1565C0; margin-bottom: 8px;'>
                {format_currency(vendedor['total_valor'])}
            </div>
            <div style='font-size: 0.75rem; color: #555; margin-bottom: 2px;'>
                Mês de {ano_anterior}=
            </div>
            <div style='font-size: 0.75rem; color: #555; margin-bottom: 6px;'>
                {format_currency(vendas_ant)}
            </div>
            <div style='font-size: 0.8rem; font-weight: 600; color: #333;'>
                {percentual:.1f}% meta do mês batida
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )


def _render_filters_and_metrics():
    """Renderiza filtros e métricas"""
    st.subheader("🔍 Filtros")

    # Inicializar dados do mês atual no primeiro carregamento
    if "df_vendas" not in st.session_state or st.session_state["df_vendas"] is None:
        _load_initial_data()

    # Filtros — widgets dentro do expander, botões fora (sempre visíveis)
    filters = None
    with st.expander("🔍 Filtros de Data e Vendedor", expanded=True):
        filter_form = FilterForm()

        # Obter listas para filtros
        try:
            loading = LoadingHelper.show_loading("Carregando opções de filtros...")
            vendedores = vendas_service.get_vendedores_ativos()
            situacoes = vendas_service.get_situacoes_disponiveis()
            origens = vendas_service.get_origens_disponiveis()
            LoadingHelper.hide_loading(loading)

            filters = filter_form.render_filters(vendedores, situacoes, origens)

        except Exception as e:
            LoadingHelper.hide_loading(loading)
            ValidationHelper.show_error(f"Erro ao carregar filtros: {str(e)}")
            return

    # Botões fora do expander — sempre visíveis independente do tamanho dos filtros
    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "🔍 Aplicar Filtros",
            type="primary",
            use_container_width=True,
            disabled=(filters is None),
            help="Aplicar os filtros selecionados",
        ):
            if filters:
                _apply_filters(filters)

    with col2:
        if st.button(
            "🔄 Recarregar Dados do Mês",
            use_container_width=True,
            help="Recarregar os dados do mês atual",
        ):
            _load_initial_data()

    st.markdown("---")

    # Renderizar métricas se houver dados
    if (
        st.session_state.get("df_vendas") is not None
        and not st.session_state["df_vendas"].empty
    ):
        # Renderizar gauge de meta PRIMEIRO (sempre com dados do mês atual)
        _render_gauge_meta()

        # Espaçamento entre Meta de Vendas e Métricas de Vendas
        st.markdown("<br><br>", unsafe_allow_html=True)

        # Container para métricas e botões de exportação
        with st.container():
            # Título e botões na mesma linha
            col_title, col_spacer, col_excel, col_csv = st.columns([3, 1, 1, 1])

            with col_title:
                st.subheader("💎 Métricas de Vendas")

            with col_excel:
                df_vendas = st.session_state.get("df_vendas", pd.DataFrame())
                if not df_vendas.empty:
                    # Preparar dados para exportação (respeitando filtros aplicados)
                    df_export = df_vendas.copy()

                    # Formatar dados para exportação Excel
                    from io import BytesIO

                    buffer_excel = BytesIO()
                    with pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:
                        df_export.to_excel(writer, index=False, sheet_name="Vendas")

                    st.download_button(
                        label="📊 Exportar Excel",
                        data=buffer_excel.getvalue(),
                        file_name=f"vendas_filtradas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="export_excel_metrics",
                    )
                else:
                    st.button(
                        "📊 Exportar Excel",
                        disabled=True,
                        use_container_width=True,
                        help="Sem dados para exportar",
                    )

            with col_csv:
                if not df_vendas.empty:
                    # Converter para CSV
                    csv_data = df_export.to_csv(index=False)

                    st.download_button(
                        label="📄 Exportar CSV",
                        data=csv_data,
                        file_name=f"vendas_filtradas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="export_csv_metrics",
                    )
                else:
                    st.button(
                        "📄 Exportar CSV",
                        disabled=True,
                        use_container_width=True,
                        help="Sem dados para exportar",
                    )

        # Renderizar os cards de métricas
        _render_metrics_cards(st.session_state.get("metricas", {}))

        # Renderizar métricas de produtos (Equipamentos vs Acessórios)
        _render_metrics_produtos()


def _load_initial_data():
    """Carrega dados iniciais do mês atual"""
    try:
        # Carregar dados do mês atual por padrão
        loading = LoadingHelper.show_loading("Carregando dados do mês atual...")
        df_vendas = vendas_service.get_vendas_mes_atual()
        LoadingHelper.hide_loading(loading)

        # Calcular métricas
        loading = LoadingHelper.show_loading("Calculando métricas...")
        metricas = vendas_service.get_metricas_vendas(df_vendas)
        LoadingHelper.hide_loading(loading)

        # Armazenar dados na sessão para uso posterior
        st.session_state["df_vendas"] = df_vendas
        st.session_state["metricas"] = metricas

        # Limpar filtros na sessão (dados do mês atual)
        # Mês atual sem filtro de situação (todas as situações)
        st.session_state["data_inicio_filtro"] = None
        st.session_state["data_fim_filtro"] = None
        st.session_state["vendedores_filtro"] = None
        st.session_state["situacoes_filtro"] = None  # Sem filtro padrão

        if df_vendas.empty:
            ValidationHelper.show_warning("Nenhum dado encontrado para o mês atual")

    except Exception as e:
        ValidationHelper.show_error(f"Erro ao carregar dados iniciais: {str(e)}")
        st.session_state["df_vendas"] = pd.DataFrame()
        st.session_state["metricas"] = {}


def _apply_filters(filters):
    """Aplica filtros personalizados"""
    try:
        # LOG: Filtros recebidos
        logger.info("=" * 50)
        logger.info("APLICANDO FILTROS - INÍCIO")
        logger.info(f"Filtros recebidos: {filters}")
        logger.info(
            f"Data Início: {filters.get('data_inicio')} (tipo: {type(filters.get('data_inicio'))})"
        )
        logger.info(
            f"Data Fim: {filters.get('data_fim')} (tipo: {type(filters.get('data_fim'))})"
        )
        logger.info(f"Vendedores: {filters.get('vendedores')}")
        logger.info(f"Situações: {filters.get('situacoes')}")

        # Validar filtros se informados
        if filters.get("data_inicio") and filters.get("data_fim"):
            if not ValidationHelper.validate_date_range(
                filters["data_inicio"], filters["data_fim"]
            ):
                return

            # Obter dados filtrados
            loading = LoadingHelper.show_loading("Carregando dados de vendas...")
            logger.info("Chamando vendas_service.get_vendas_filtradas...")
            df_vendas = vendas_service.get_vendas_filtradas(
                data_inicio=filters["data_inicio"],
                data_fim=filters["data_fim"],
                vendedores=filters["vendedores"] if filters["vendedores"] else None,
                situacoes=filters["situacoes"] if filters["situacoes"] else None,
                origens=filters.get("origens") if filters.get("origens") else None,
            )
            LoadingHelper.hide_loading(loading)

            # LOG: Dados retornados
            logger.info(f"Dados retornados: {len(df_vendas)} registros")
            if not df_vendas.empty:
                logger.info(f"Colunas: {df_vendas.columns.tolist()}")
                if "VendedorNome" in df_vendas.columns:
                    vendedores_unicos = df_vendas["VendedorNome"].unique().tolist()
                    logger.info(f"Vendedores únicos nos dados: {vendedores_unicos}")
                if "Data" in df_vendas.columns:
                    try:
                        datas = pd.to_datetime(df_vendas["Data"], errors="coerce")
                        logger.info(f"Data mínima: {datas.min()}")
                        logger.info(f"Data máxima: {datas.max()}")
                    except:
                        logger.info("Erro ao processar datas")
            logger.info("=" * 50)
        else:
            ValidationHelper.show_error("Por favor, informe as datas de início e fim")
            return

        # Calcular métricas
        loading = LoadingHelper.show_loading("Calculando métricas...")
        metricas = vendas_service.get_metricas_vendas(df_vendas)
        LoadingHelper.hide_loading(loading)

        # Armazenar dados na sessão para uso posterior
        st.session_state["df_vendas"] = df_vendas
        st.session_state["metricas"] = metricas

        # Armazenar filtros aplicados na sessão
        st.session_state["data_inicio_filtro"] = filters["data_inicio"]
        st.session_state["data_fim_filtro"] = filters["data_fim"]
        st.session_state["vendedores_filtro"] = (
            filters["vendedores"] if filters["vendedores"] else None
        )
        st.session_state["situacoes_filtro"] = (
            filters["situacoes"] if filters["situacoes"] else None
        )

        if df_vendas.empty:
            ValidationHelper.show_warning(
                "Nenhum dado encontrado para os filtros selecionados"
            )
        else:
            st.rerun()

    except ValidationError as e:
        ValidationHelper.show_error(f"Erro de validação: {str(e)}")
    except BusinessLogicError as e:
        ValidationHelper.show_error(f"Erro de negócio: {str(e)}")
    except Exception as e:
        ValidationHelper.show_error(f"Erro inesperado: {str(e)}")
        logger.error(f"Erro ao aplicar filtros: {str(e)}")


def _render_download_section():
    """Renderiza seção de download dos dados"""
    # Espaçamento antes da seção de download
    st.markdown("<br><br>", unsafe_allow_html=True)

    st.subheader("📥 Download dos Dados")

    # Verificar se há dados disponíveis
    has_data = (
        "df_vendas" in st.session_state
        and st.session_state["df_vendas"] is not None
        and not st.session_state["df_vendas"].empty
    )

    col1, col2, col3 = st.columns(3)

    if has_data:
        df = st.session_state["df_vendas"]

        with col1:
            # Download Excel
            from io import BytesIO

            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df.to_excel(writer, sheet_name="Vendas", index=False)

            st.download_button(
                label="📊 Download Excel",
                data=buffer.getvalue(),
                file_name=f"vendas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with col2:
            # Download CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="📄 Download CSV",
                data=csv,
                file_name=f"vendas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col3:
            st.markdown(
                f"""
            <div style='
                height: 38px; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                background-color: #d1ecf1; 
                border: 1px solid #bee5eb; 
                border-radius: 0.25rem; 
                color: #0c5460; 
                font-weight: 500;
            '>
                📊 {len(df)} registros
            </div>
            """,
                unsafe_allow_html=True,
            )
    else:
        # Mostrar botões desabilitados se não há dados
        with col1:
            st.button("📊 Download Excel", disabled=True, use_container_width=True)

        with col2:
            st.button("📄 Download CSV", disabled=True, use_container_width=True)

        with col3:
            st.markdown(
                """
            <div style='
                height: 38px; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                background-color: #d1ecf1; 
                border: 1px solid #bee5eb; 
                border-radius: 0.25rem; 
                color: #0c5460; 
                font-weight: 500;
            '>
                📊 Nenhum dado carregado
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("---")


def _render_charts():
    """Renderiza gráficos de análise"""
    if "df_vendas" not in st.session_state or st.session_state["df_vendas"] is None:
        return

    df_vendas = st.session_state["df_vendas"]

    if df_vendas.empty:
        st.warning("Não há dados para exibir gráficos")
        return

    st.subheader("📈 Análise por Vendedor")

    # Obter dados agregados por vendedor
    vendas_por_vendedor = vendas_service.get_vendas_por_vendedor(df_vendas, top_n=10)

    if not vendas_por_vendedor.empty:
        # Primeiro gráfico - Distribuição por Valor (Pizza)
        st.subheader("📊 Distribuição por Valor")
        fig_pie = _create_pie_chart(vendas_por_vendedor)
        st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")

        # Segundo gráfico - Quantidade por Vendedor (Barras)
        st.subheader("📈 Quantidade por Vendedor")
        fig_bar = _create_bar_chart(vendas_por_vendedor)
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")

        # Terceiro gráfico - Ranking de Vendedores
        st.subheader("🏆 Ranking de Vendedores")

        try:
            _render_vendedores_com_fotos(vendas_por_vendedor)
        except Exception as e:
            logger.error(f"Erro ao renderizar vendedores com fotos: {str(e)}")
            st.error(f"Erro ao exibir vendedores: {str(e)}")

    st.markdown("---")

    # Quarto painel - Ranking de Produtos Mais Vendidos
    st.subheader("🏆 Ranking de Produtos")

    try:
        # Obter IDs de vendas do DataFrame já carregado (mais eficiente)
        venda_ids = None
        if "ID_Gestao" in df_vendas.columns and not df_vendas.empty:
            venda_ids = df_vendas["ID_Gestao"].tolist()
            # Só usar venda_ids se a lista não estiver vazia
            if not venda_ids:
                venda_ids = None

        # Obter filtros aplicados da sessão (para fallback)
        data_inicio = st.session_state.get("data_inicio_filtro")
        data_fim = st.session_state.get("data_fim_filtro")
        vendedores = st.session_state.get("vendedores_filtro")
        situacoes = st.session_state.get("situacoes_filtro")

        # Obter ranking de produtos
        ranking_produtos = _get_ranking_produtos(
            data_inicio=data_inicio,
            data_fim=data_fim,
            vendedores=vendedores,
            situacoes=situacoes,
            venda_ids=venda_ids,
            top_n=10,
        )

        # Renderizar cards do ranking
        _render_ranking_produtos(ranking_produtos)

    except Exception as e:
        logger.error(f"Erro ao renderizar ranking de produtos: {str(e)}")
        st.error(f"Erro ao exibir ranking de produtos: {str(e)}")

    st.markdown("---")


def _render_manual_fullscreen():
    """Renderiza o manual em tela cheia"""
    try:
        # Aplicar tema
        apply_theme()

        # Ler arquivo do manual primeiro
        manual_path = "documentacao/Manual_Relatorio_Vendas.md"
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
            '<h1 class="manual-title">📖 Manual do Relatório de Vendas</h1>'
            "</div>",
            unsafe_allow_html=True,
        )

        # Botões de ação centralizados
        col1, col2, col3, col4, col5 = st.columns([2, 1.5, 0.5, 1.5, 2])

        with col2:
            st.download_button(
                label="📥 Download Manual",
                data=content,
                file_name="Manual_Relatorio_Vendas.md",
                mime="text/markdown",
                key="download_manual_fullscreen",
                use_container_width=True,
            )

        with col4:
            if st.button(
                "⬅️ Voltar ao Dashboard",
                key="back_to_dashboard",
                use_container_width=True,
            ):
                st.session_state["view_mode"] = "dashboard"
                st.rerun()

        st.markdown("---")

        # Exibir conteúdo do manual diretamente
        st.markdown(content)

    except FileNotFoundError:
        st.error(
            f"❌ Arquivo do manual não encontrado: documentacao/Manual_Relatorio_Vendas.md"
        )
    except Exception as e:
        st.error(f"❌ Erro ao carregar manual: {str(e)}")


def _render_data_grid():
    """Renderiza grid de vendas detalhadas com AgGrid avançado"""
    if "df_vendas" not in st.session_state or st.session_state["df_vendas"] is None:
        return

    df_vendas = st.session_state["df_vendas"]

    if df_vendas.empty:
        st.info("Nenhum dado disponível para exibição")
        return

    st.subheader("📋 Vendas Detalhadas")

    # Preparar dados para exibição — incluir Origem se disponível no dataset
    colunas_display = [
        "ClienteNome",
        "VendedorNome",
        "ValorProdutos",
        "ValorDesconto",
        "ValorTotal",
        "Data",
    ]
    if "Origem" in df_vendas.columns:
        colunas_display.append("Origem")

    df_display = df_vendas[colunas_display].copy()

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
            # Remover pontos (separador de milhares) e trocar vírgula por ponto
            val_clean = val_str.replace(".", "").replace(",", ".")
        else:
            # Formato americano ou já limpo (1500.00 ou 1500)
            val_clean = val_str

        val_clean = val_clean.strip()
        try:
            return float(val_clean) if val_clean else 0.0
        except:
            return 0.0

    # Garantir que valores monetários sejam float (sem formatação - AgGrid fará a formatação visual)
    for col in ["ValorProdutos", "ValorDesconto", "ValorTotal"]:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(clean_monetary_value)

    # Formatar coluna Data para exibir apenas dd/mm/yyyy (sem horário)
    def format_date(val):
        """Formata data para dd/mm/yyyy sem horário"""
        if pd.isna(val):
            return ""
        try:
            if isinstance(val, str):
                # Se já é string, tentar parsear
                if "/" in val:
                    # Formato brasileiro dd/mm/yyyy ou dd/mm/yyyy HH:MM
                    parts = val.split()[
                        0
                    ]  # Remove horário se houver (pega só a data antes do espaço)
                    return parts
                else:
                    # Formato ISO ou outro, converter para datetime
                    dt = pd.to_datetime(val)
                    return dt.strftime("%d/%m/%Y")
            elif isinstance(val, (datetime, pd.Timestamp)):
                return val.strftime("%d/%m/%Y")
            elif isinstance(val, date):
                return val.strftime("%d/%m/%Y")
            else:
                return str(val)
        except:
            return str(val)

    if "Data" in df_display.columns:
        df_display["Data"] = df_display["Data"].apply(format_date)

    # Renomear colunas (Origem não precisa de renomeação)
    rename_map = {
        "ClienteNome": "Cliente",
        "VendedorNome": "Vendedor",
        "ValorProdutos": "Valor Produtos",
        "ValorDesconto": "Desconto",
        "ValorTotal": "Valor Total",
        "Data": "Data",
    }
    df_display.rename(columns=rename_map, inplace=True)

    # Renderizar grid avançada com AgGrid e capturar dados filtrados
    df_filtered = _render_advanced_sales_grid(df_display, df_vendas)

    # Armazenar IDs das vendas filtradas na grid para uso no painel de Produtos
    if df_filtered is not None and not df_filtered.empty:
        # Mapear vendas filtradas de volta ao df original para pegar os IDs
        # Criar chave única para matching
        df_vendas_with_key = df_vendas.copy()
        df_vendas_with_key["_match_key"] = (
            df_vendas_with_key["ClienteNome"].astype(str)
            + "|"
            + df_vendas_with_key["VendedorNome"].astype(str)
            + "|"
            + df_vendas_with_key["ValorTotal"].astype(str)
            + "|"
            + df_vendas_with_key["Data"].astype(str)
        )

        df_filtered_with_key = df_filtered.copy()
        df_filtered_with_key["_match_key"] = (
            df_filtered_with_key["Cliente"].astype(str)
            + "|"
            + df_filtered_with_key["Vendedor"].astype(str)
            + "|"
            + df_filtered_with_key["Valor Total"]
            .apply(lambda x: str(x) if isinstance(x, (int, float)) else str(x))
            .astype(str)
            + "|"
            + df_filtered_with_key["Data"].astype(str)
        )

        # Encontrar IDs das vendas filtradas
        vendas_filtradas = df_vendas_with_key[
            df_vendas_with_key["_match_key"].isin(df_filtered_with_key["_match_key"])
        ]

        if "Id" in vendas_filtradas.columns:
            ids_vendas_filtradas = vendas_filtradas["Id"].tolist()
        elif "ID_Gestao" in vendas_filtradas.columns:
            ids_vendas_filtradas = vendas_filtradas["ID_Gestao"].tolist()
        else:
            ids_vendas_filtradas = None

        st.session_state["ids_vendas_grid_filtradas"] = ids_vendas_filtradas
    else:
        st.session_state["ids_vendas_grid_filtradas"] = None


def _render_advanced_sales_grid(df_display, df_original):
    """Renderiza grid avançada de vendas usando AgGrid com funcionalidades completas"""
    from st_aggrid import AgGrid, GridOptionsBuilder

    # Interface para seleção de colunas visíveis
    st.markdown("#### 👁️ Colunas Visíveis")

    # Inicializar ou atualizar estado das colunas visíveis
    # Garante que novas colunas (ex: Origem) sejam sempre incluídas no default
    colunas_atuais = list(df_display.columns)
    if "vendas_visible_columns" not in st.session_state:
        st.session_state["vendas_visible_columns"] = colunas_atuais
    else:
        # Adicionar colunas novas que ainda não estavam no estado salvo
        colunas_salvas = st.session_state["vendas_visible_columns"]
        novas_colunas = [c for c in colunas_atuais if c not in colunas_salvas]
        if novas_colunas:
            st.session_state["vendas_visible_columns"] = colunas_salvas + novas_colunas

    # Garantir que apenas colunas existentes no df atual sejam usadas como default
    default_valido = [
        c for c in st.session_state["vendas_visible_columns"] if c in colunas_atuais
    ]

    # Multiselect para escolher colunas visíveis
    selected_columns = st.multiselect(
        "Selecione as colunas para exibir e exportar:",
        options=colunas_atuais,
        default=default_valido,
        key="vendas_columns_selector",
    )

    # Atualizar estado das colunas visíveis
    st.session_state["vendas_visible_columns"] = selected_columns

    # Filtrar DataFrame para mostrar apenas colunas selecionadas
    if selected_columns:
        df_display_filtered = df_display[selected_columns]
    else:
        df_display_filtered = df_display
        st.warning("⚠️ Nenhuma coluna selecionada. Mostrando todas.")

    st.markdown("---")

    def create_sales_grid_options(df):
        """Cria configurações para a grid de vendas"""
        gb = GridOptionsBuilder.from_dataframe(df)

        gb.configure_grid_options(
            domLayout="normal",
            enableRangeSelection=True,
            enableCellTextSelection=True,
            suppressRowClickSelection=True,
            onFirstDataRendered="onFirstDataRendered",
            onFilterChanged="onFilterChanged",
        )

        # Configurações de coluna
        gb.configure_default_column(
            filter=True, cellStyle={"border": "1px solid black"}, floatingFilter=True
        )

        # Configuração dos cabeçalhos e formatação personalizada
        for col in df.columns:
            if col == "Cliente":
                gb.configure_column(col, headerName="Cliente")
            elif col == "Vendedor":
                gb.configure_column(col, headerName="Vendedor")
            elif col == "Data":
                gb.configure_column(col, headerName="Data")
            elif "Valor" in col or col == "Desconto":
                gb.configure_column(
                    col,
                    headerName=col,
                    type=["numericColumn", "numberColumnFilter"],
                    valueFormatter="'R$ ' + x.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})",
                )
            elif col == "Origem":
                gb.configure_column(
                    col,
                    headerName="Origem",
                    width=150,
                    filter=True,
                    floatingFilter=True,
                    sortable=True,
                    hide=False,
                )
            else:
                gb.configure_column(col, headerName=col)

        # Totalizadores
        for col in df.columns:
            if "Valor" in col or col == "Desconto":
                gb.configure_column(col, aggFunc="sum", header_name=f"Total {col}")

        return gb.build()

    # Calcular totalizadores
    def calculate_sales_totals(data):
        totals = {"total_vendas": len(data)}

        # Calcular totais de valores monetários
        for col in data.columns:
            if "Valor" in col or col == "Desconto":
                try:
                    # Valores já são numéricos, apenas somar
                    totals[f"total_{col.lower().replace(' ', '_')}"] = (
                        pd.to_numeric(data[col], errors="coerce").fillna(0).sum()
                    )
                except:
                    totals[f"total_{col.lower().replace(' ', '_')}"] = 0

        return totals

    # Exibir totalizadores
    def display_sales_totals(totals, df_filtered):
        from io import BytesIO

        container = st.container()
        with container:
            # Dividindo em colunas para totalizadores e botões
            cols = st.columns([2, 2, 2, 1, 1])

            with cols[0]:
                st.metric("📊 Total Vendas", totals["total_vendas"])

            # Exibir valores monetários prioritários
            col_idx = 1
            priority_cols = [
                "total_valor_total",
                "total_desconto",
                "total_valor_produtos",
            ]

            for priority_col in priority_cols:
                if priority_col in totals and col_idx < 3:
                    with cols[col_idx]:
                        col_name = (
                            priority_col.replace("total_", "").replace("_", " ").title()
                        )
                        if priority_col == "total_desconto":
                            col_name = "Desconto"
                            icon = "💳"
                        elif priority_col == "total_valor_total":
                            col_name = "Valor Total"
                            icon = "💰"
                        elif priority_col == "total_valor_produtos":
                            col_name = "Valor Produtos"
                            icon = "📦"
                        else:
                            icon = "💰"

                        value = totals[priority_col]
                        st.metric(
                            f"{icon} {col_name}",
                            f"R$ {value:,.2f}".replace(",", "X")
                            .replace(".", ",")
                            .replace("X", "."),
                        )
                    col_idx += 1

            # Botões de download - usando dados filtrados da grid
            with cols[3]:
                st.write("")  # Espaço para alinhar
                if not df_filtered.empty:
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        df_filtered.to_excel(
                            writer, index=False, sheet_name="Vendas_Detalhadas"
                        )

                    if st.download_button(
                        label="📊 Excel",
                        data=buffer.getvalue(),
                        file_name=f"vendas_detalhadas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="download_excel_vendas",
                    ):
                        st.success("Excel baixado!")
                else:
                    st.button(
                        "📊 Excel",
                        disabled=True,
                        use_container_width=True,
                        help="Sem dados para exportar",
                    )

            with cols[4]:
                st.write("")  # Espaço para alinhar
                if not df_filtered.empty:
                    csv_data = df_filtered.to_csv(index=False)

                    if st.download_button(
                        label="📄 CSV",
                        data=csv_data,
                        file_name=f"vendas_detalhadas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="download_csv_vendas",
                    ):
                        st.success("CSV baixado!")
                else:
                    st.button(
                        "📄 CSV",
                        disabled=True,
                        use_container_width=True,
                        help="Sem dados para exportar",
                    )

    # Container para os totalizadores
    totals_container = st.container()

    # Renderizar o grid com colunas filtradas
    with st.spinner("Carregando grid..."):
        # IMPORTANTE: Criar key dinâmica para forçar re-renderização quando filtros mudarem
        # Usar hash dos filtros aplicados + timestamp para garantir atualização
        import hashlib

        filtros_str = f"{st.session_state.get('data_inicio_filtro')}_{st.session_state.get('data_fim_filtro')}_{st.session_state.get('vendedores_filtro')}_{st.session_state.get('situacoes_filtro')}_{len(df_display_filtered)}"
        grid_key = f"vendas_grid_{hashlib.md5(filtros_str.encode()).hexdigest()}"

        grid_options = create_sales_grid_options(df_display_filtered)
        grid_response = AgGrid(
            df_display_filtered,
            gridOptions=grid_options,
            height=800,
            fit_columns_on_grid_load=True,
            theme="alpine",
            allow_unsafe_jscode=True,
            reload_data=True,
            key=grid_key,  # Key dinâmica que muda com os filtros
            columns_auto_size_mode="FIT_CONTENTS",
        )

    # Calcular e exibir totalizadores - usando dados filtrados da grid
    df_filtered_sales = pd.DataFrame(grid_response["data"])

    # Como estamos usando multiselect para controlar colunas visíveis,
    # os dados da grid já contêm apenas as colunas selecionadas
    df_export_sales = df_filtered_sales

    totals = calculate_sales_totals(df_filtered_sales)

    with totals_container:
        display_sales_totals(totals, df_export_sales)

    st.markdown("---")

    return grid_response["data"]


def _create_pie_chart(df):
    """Cria gráfico de pizza"""
    import plotly.express as px
    import plotly.graph_objects as go

    # Calcular percentuais
    total = df["total_valor"].sum()
    df["percentual"] = (df["total_valor"] / total * 100).round(1)

    # Definir cores consistentes para cada vendedor
    colors = px.colors.qualitative.Set3[: len(df)]

    # Criar labels customizados com valor e percentual
    labels_customizados = []
    for i, row in df.iterrows():
        valor_formatado = (
            f"R$ {row['total_valor']:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        labels_customizados.append(
            f"{row['VendedorNome']}<br>{valor_formatado} ({row['percentual']}%)"
        )

    fig = px.pie(
        df,
        values="total_valor",
        names="VendedorNome",
        title="Distribuição de Vendas por Vendedor (Valor)",
        color_discrete_sequence=px.colors.sequential.Blues,
        hole=0.4,
    )

    fig.update_layout(
        legend_title="Vendedores",
        legend=dict(orientation="v", yanchor="middle", y=0.5),
        margin=dict(t=50, b=50, l=10, r=10),
        height=400,
    )

    return fig


def _create_bar_chart(df):
    """Cria gráfico de barras"""
    import plotly.express as px

    fig = px.bar(
        df,
        x="VendedorNome",
        y="quantidade",
        title="Quantidade de Vendas por Vendedor",
        color="quantidade",
        color_continuous_scale="Blues",
    )

    fig.update_layout(
        xaxis_title="Vendedor",
        yaxis_title="Quantidade",
        xaxis_tickangle=-45,
        height=400,
    )

    return fig


def _create_value_percentage_chart(df):
    """Cria gráfico de barras com valor e percentual"""
    try:
        import plotly.express as px

        if df is None or df.empty:
            return None

        if "total_valor" not in df.columns or "VendedorNome" not in df.columns:
            return None

        # Calcular percentuais
        total_geral = float(df["total_valor"].sum())
        if total_geral <= 0:
            return None

        # Preparar dados simples
        df_chart = df.copy()
        df_chart["percentual"] = (df_chart["total_valor"] / total_geral * 100).round(1)

        # Gráfico simples com plotly express
        fig = px.bar(
            df_chart,
            x="VendedorNome",
            y="total_valor",
            title="💰 Valor de Vendas por Vendedor",
            labels={"VendedorNome": "Vendedor", "total_valor": "Valor (R$)"},
            color="total_valor",
            color_continuous_scale="Blues",
        )

        # Customizar layout
        fig.update_layout(
            xaxis_tickangle=-45, height=450, showlegend=False, coloraxis_showscale=False
        )

        # Adicionar texto nas barras com fundo azul escuro
        for i, row in df_chart.iterrows():
            fig.add_annotation(
                x=row["VendedorNome"],
                y=row["total_valor"] / 2,
                text=f"R$ {float(row['total_valor']):,.0f}<br>{row['percentual']:.1f}%".replace(
                    ",", "."
                ),
                showarrow=False,
                font=dict(color="white", size=12, family="Arial Black"),
                bgcolor="#1565C0",
                bordercolor="#0D47A1",
                borderwidth=1,
            )

        return fig

    except Exception:
        return None


def _get_ranking_produtos(
    data_inicio, data_fim, vendedores=None, situacoes=None, venda_ids=None, top_n=10
):
    """
    Obtém o ranking dos produtos mais vendidos no período

    Args:
        data_inicio: Data inicial do período
        data_fim: Data final do período
        vendedores: Lista de vendedores (opcional)
        situacoes: Lista de situações (opcional)
        venda_ids: Lista de IDs de vendas (opcional - mais eficiente)
        top_n: Número de produtos no ranking (padrão 10)

    Returns:
        pd.DataFrame com colunas: ProdutoNome, TotalQuantidade, NumeroVendas
    """
    try:
        # IMPORTANTE: Se temos venda_ids, eles já representam as vendas filtradas
        # Portanto, NÃO devemos passar outros filtros para evitar conflitos
        if venda_ids:
            # Usar APENAS venda_ids (que já vem do df_vendas filtrado)
            logger.info(f"DEBUG Ranking - Usando venda_ids: {len(venda_ids)} vendas")
            df_produtos = vendas_service.get_produtos_detalhados(
                venda_ids=venda_ids,
                excluir_grupos=True,
            )
        else:
            # Fallback: usar filtros de data/vendedor/situação se não temos venda_ids
            # Converter para datetime se necessário
            if data_inicio and not isinstance(data_inicio, datetime):
                if isinstance(data_inicio, str):
                    data_inicio = datetime.strptime(str(data_inicio), "%Y-%m-%d")
                elif isinstance(data_inicio, date):
                    data_inicio = datetime.combine(data_inicio, datetime.min.time())

            if data_fim and not isinstance(data_fim, datetime):
                if isinstance(data_fim, str):
                    data_fim = datetime.strptime(str(data_fim), "%Y-%m-%d")
                elif isinstance(data_fim, date):
                    data_fim = datetime.combine(data_fim, datetime.min.time())

            logger.info(
                f"DEBUG Ranking - data_inicio: {data_inicio}, data_fim: {data_fim}"
            )
            logger.info(
                f"DEBUG Ranking - vendedores: {vendedores}, situacoes: {situacoes}"
            )

            # Obter produtos DETALHADOS (não agregados) para contar vendas corretamente
            # Excluir grupos: PRODUTOS SEM GRUPO, PEÇA DE REPOSIÇÃO, ACESSÓRIOS
            df_produtos = vendas_service.get_produtos_detalhados(
                data_inicio=data_inicio,
                data_fim=data_fim,
                vendedores=vendedores,
                situacoes=situacoes,
                venda_ids=None,
                excluir_grupos=True,
            )

        logger.info(f"DEBUG Ranking - df_produtos shape: {df_produtos.shape}")
        logger.info(
            f"DEBUG Ranking - df_produtos columns: {df_produtos.columns.tolist() if not df_produtos.empty else 'EMPTY'}"
        )

        if df_produtos.empty:
            logger.warning("DEBUG Ranking - DataFrame de produtos está vazio")
            return pd.DataFrame()

        # Debug: Mostrar primeiras linhas
        logger.info(f"DEBUG Ranking - Primeiras linhas:\n{df_produtos.head()}")

        # Verificar qual coluna de nome do produto existe
        nome_coluna = None
        if "Nome" in df_produtos.columns:
            nome_coluna = "Nome"
        elif "ProdutoNome" in df_produtos.columns:
            nome_coluna = "ProdutoNome"
        else:
            logger.error(
                f"DEBUG Ranking - Nenhuma coluna de nome de produto encontrada. Colunas disponíveis: {df_produtos.columns.tolist()}"
            )
            return pd.DataFrame()

        logger.info(f"DEBUG Ranking - Usando coluna: {nome_coluna}")

        # Agrupar por produto e calcular totais
        # Usar produtos detalhados para contar vendas distintas corretamente
        ranking = (
            df_produtos.groupby(nome_coluna)
            .agg(
                TotalQuantidade=("Quantidade", "sum"),
                NumeroVendas=(
                    "Venda_ID",
                    "nunique",
                ),  # Contar vendas DISTINTAS por produto
            )
            .reset_index()
        )

        # Renomear coluna para padrão
        ranking.rename(columns={nome_coluna: "ProdutoNome"}, inplace=True)

        logger.info(f"DEBUG Ranking - ranking shape após groupby: {ranking.shape}")
        logger.info(f"DEBUG Ranking - ranking head:\n{ranking.head()}")

        # Ordenar por quantidade total vendida (decrescente)
        ranking = ranking.sort_values("TotalQuantidade", ascending=False)

        # Limitar ao top_n
        ranking = ranking.head(top_n)

        logger.info(f"DEBUG Ranking - ranking final shape: {ranking.shape}")
        return ranking

    except Exception as e:
        logger.error(f"Erro ao obter ranking de produtos: {str(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return pd.DataFrame()


def _render_ranking_produtos(ranking_df):
    """
    Renderiza cards com o ranking dos produtos mais vendidos

    Args:
        ranking_df: DataFrame com colunas ProdutoNome, TotalQuantidade, NumeroVendas
    """
    if ranking_df.empty:
        st.info("📦 Nenhum produto encontrado para o período selecionado")
        return

    # CSS para os cards de produtos - Melhorado com contraste superior
    st.markdown(
        """
        <style>
        .produto-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            height: 100%;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            color: white;
        }

        .produto-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba(0,0,0,0.2);
        }

        .produto-rank {
            font-size: 2.5em;
            font-weight: bold;
            opacity: 0.4;
            line-height: 1;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .produto-nome {
            font-size: 1.1em;
            font-weight: 700;
            margin-bottom: 15px;
            min-height: 48px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.4);
            line-height: 1.3;
        }

        .produto-metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 8px 0;
            padding: 10px 14px;
            background: rgba(0,0,0,0.25);
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.2);
        }

        .produto-metric-label {
            font-size: 0.95em;
            font-weight: 600;
            opacity: 1;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }

        .produto-metric-value {
            font-size: 1.4em;
            font-weight: 900;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.4);
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # Renderizar cards em grid 5x2 (5 colunas, 2 linhas)
    for linha in range(2):
        cols = st.columns(5)
        for col_idx, col in enumerate(cols):
            produto_idx = linha * 5 + col_idx

            if produto_idx < len(ranking_df):
                produto = ranking_df.iloc[produto_idx]
                rank = produto_idx + 1

                with col:
                    # Determinar cor do gradiente baseado na posição
                    if rank == 1:
                        gradient = (
                            "linear-gradient(135deg, #FFD700 0%, #FFA500 100%)"  # Ouro
                        )
                    elif rank == 2:
                        gradient = (
                            "linear-gradient(135deg, #C0C0C0 0%, #808080 100%)"  # Prata
                        )
                    elif rank == 3:
                        gradient = "linear-gradient(135deg, #CD7F32 0%, #8B4513 100%)"  # Bronze
                    else:
                        gradient = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"  # Padrão

                    st.markdown(
                        f"""
                        <div class="produto-card" style="background: {gradient};">
                            <div class="produto-rank">#{rank}</div>
                            <div class="produto-nome" title="{produto['ProdutoNome']}">
                                {produto['ProdutoNome']}
                            </div>
                            <div class="produto-metric">
                                <span class="produto-metric-label">📦 Qtd. Total</span>
                                <span class="produto-metric-value">{int(produto['TotalQuantidade'])}</span>
                            </div>
                            <div class="produto-metric">
                                <span class="produto-metric-label">🛒 Nº Vendas</span>
                                <span class="produto-metric-value">{int(produto['NumeroVendas'])}</span>
                            </div>
                        </div>
                    """,
                        unsafe_allow_html=True,
                    )

        # Adicionar espaçamento entre linha 1 e linha 2
        if linha == 0:
            st.markdown(
                "<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True
            )


def _render_advanced_products_grid(df_display):
    """Renderiza grid avançada usando AgGrid com funcionalidades completas"""
    from st_aggrid import AgGrid, GridOptionsBuilder

    # Interface para seleção de colunas visíveis
    st.markdown("#### 👁️ Colunas Visíveis")

    # Inicializar estado das colunas visíveis se não existir
    if "produtos_visible_columns" not in st.session_state:
        st.session_state["produtos_visible_columns"] = list(df_display.columns)

    # Multiselect para escolher colunas visíveis
    selected_columns = st.multiselect(
        "Selecione as colunas para exibir e exportar:",
        options=list(df_display.columns),
        default=st.session_state["produtos_visible_columns"],
        key="produtos_columns_selector",
    )

    # Atualizar estado das colunas visíveis
    st.session_state["produtos_visible_columns"] = selected_columns

    # Filtrar DataFrame para mostrar apenas colunas selecionadas
    if selected_columns:
        df_display_filtered = df_display[selected_columns]
    else:
        df_display_filtered = df_display
        st.warning("⚠️ Nenhuma coluna selecionada. Mostrando todas.")

    st.markdown("---")

    def create_products_grid_options(df):
        """Cria configurações para a grid de produtos"""
        gb = GridOptionsBuilder.from_dataframe(df)

        gb.configure_grid_options(
            domLayout="normal",
            enableRangeSelection=True,
            enableCellTextSelection=True,
            suppressRowClickSelection=True,
            onFirstDataRendered="onFirstDataRendered",
            onFilterChanged="onFilterChanged",
        )

        # Configurações de coluna
        gb.configure_default_column(
            filter=True, cellStyle={"border": "1px solid black"}, floatingFilter=True
        )

        # Configuração dos cabeçalhos e formatação personalizada
        for col in df.columns:
            if col == "Produto":
                gb.configure_column(col, headerName="Produto")
            elif col == "Código Expedição":
                gb.configure_column(col, headerName="Código Expedição")
            elif col == "Quantidade":
                gb.configure_column(
                    col,
                    headerName="Quantidade",
                    type=["numericColumn", "numberColumnFilter"],
                    valueFormatter="x.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})",
                )
            elif "Valor" in col:
                gb.configure_column(
                    col,
                    headerName=col,
                    type=["numericColumn", "numberColumnFilter"],
                    valueFormatter="'R$ ' + x.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})",
                )
            else:
                gb.configure_column(col, headerName=col)

        # Totalizadores
        if "Quantidade" in df.columns:
            gb.configure_column(
                "Quantidade", aggFunc="sum", header_name="Total Quantidade"
            )
        for col in df.columns:
            if "Valor" in col:
                gb.configure_column(col, aggFunc="sum", header_name=f"Total {col}")

        return gb.build()

    # Calcular totalizadores
    def calculate_products_totals(data):
        totals = {"total_produtos": len(data)}

        if "Quantidade" in data.columns:
            try:
                # Valores já são numéricos, apenas somar
                totals["total_quantidade"] = (
                    pd.to_numeric(data["Quantidade"], errors="coerce").fillna(0).sum()
                )
            except:
                totals["total_quantidade"] = 0

        # Calcular totais de valores monetários
        for col in data.columns:
            if "Valor" in col:
                try:
                    # Valores já são numéricos, apenas somar
                    totals[f"total_{col.lower().replace(' ', '_')}"] = (
                        pd.to_numeric(data[col], errors="coerce").fillna(0).sum()
                    )
                except:
                    totals[f"total_{col.lower().replace(' ', '_')}"] = 0

        return totals

    # Exibir totalizadores
    def display_products_totals(totals, df_filtered):
        from io import BytesIO

        container = st.container()
        with container:
            # Dividindo em colunas para totalizadores e botões
            cols = st.columns([2, 2, 2, 1, 1])

            with cols[0]:
                st.metric("📊 Total Produtos", totals["total_produtos"])

            if "total_quantidade" in totals:
                with cols[1]:
                    st.metric(
                        "📦 Quantidade Total",
                        f"{int(totals['total_quantidade']):,}".replace(",", "."),
                    )

            # Exibir valores monetários (usando apenas cols[2] para não ocupar espaço dos botões)
            col_idx = 2
            valor_cols_count = sum(
                1 for key in totals.keys() if key.startswith("total_valor")
            )

            if valor_cols_count > 0:
                with cols[2]:
                    # Se houver múltiplos valores monetários, mostrar apenas o mais relevante ou uma síntese
                    if "total_valor_desconto" in totals:
                        value = totals["total_valor_desconto"]
                        st.metric(
                            "💳 Valor Desconto",
                            f"R$ {value:,.2f}".replace(",", "X")
                            .replace(".", ",")
                            .replace("X", "."),
                        )
                    else:
                        # Pegar o primeiro valor monetário encontrado
                        for key, value in totals.items():
                            if key.startswith("total_valor"):
                                col_name = (
                                    key.replace("total_valor_", "")
                                    .replace("_", " ")
                                    .title()
                                )
                                st.metric(
                                    f"💰 {col_name}",
                                    f"R$ {value:,.2f}".replace(",", "X")
                                    .replace(".", ",")
                                    .replace("X", "."),
                                )
                                break

            # Botões de download - usando dados filtrados da grid
            with cols[3]:
                st.write("")  # Espaço para alinhar
                if not df_filtered.empty:
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        df_filtered.to_excel(
                            writer, index=False, sheet_name="Produtos_Detalhados"
                        )

                    if st.download_button(
                        label="📊 Excel",
                        data=buffer.getvalue(),
                        file_name=f"produtos_detalhados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="download_excel_produtos",
                    ):
                        st.success("Excel baixado!")
                else:
                    st.button(
                        "📊 Excel",
                        disabled=True,
                        use_container_width=True,
                        help="Sem dados para exportar",
                    )

            with cols[4]:
                st.write("")  # Espaço para alinhar
                if not df_filtered.empty:
                    csv_data = df_filtered.to_csv(index=False)

                    if st.download_button(
                        label="📄 CSV",
                        data=csv_data,
                        file_name=f"produtos_detalhados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="download_csv_produtos",
                    ):
                        st.success("CSV baixado!")
                else:
                    st.button(
                        "📄 CSV",
                        disabled=True,
                        use_container_width=True,
                        help="Sem dados para exportar",
                    )

    # Container para os totalizadores
    totals_container = st.container()

    # Renderizar o grid com colunas filtradas
    with st.spinner("Carregando grid..."):
        # IMPORTANTE: Criar key dinâmica para forçar re-renderização quando filtros mudarem
        import hashlib

        filtros_str = f"{st.session_state.get('data_inicio_filtro')}_{st.session_state.get('data_fim_filtro')}_{st.session_state.get('vendedores_filtro')}_{st.session_state.get('situacoes_filtro')}_{len(df_display_filtered)}"
        grid_key = f"produtos_grid_{hashlib.md5(filtros_str.encode()).hexdigest()}"

        grid_options = create_products_grid_options(df_display_filtered)
        grid_response = AgGrid(
            df_display_filtered,
            gridOptions=grid_options,
            height=800,
            fit_columns_on_grid_load=True,
            theme="alpine",
            allow_unsafe_jscode=True,
            reload_data=True,
            key=grid_key,  # Key dinâmica que muda com os filtros
        )

    # Calcular e exibir totalizadores - usando dados filtrados da grid
    df_filtered_products = pd.DataFrame(grid_response["data"])

    # Como estamos usando multiselect para controlar colunas visíveis,
    # os dados da grid já contêm apenas as colunas selecionadas
    df_export_products = df_filtered_products

    totals = calculate_products_totals(df_filtered_products)

    with totals_container:
        display_products_totals(totals, df_export_products)

    st.markdown("---")

    return grid_response["data"]


def _render_produtos_detalhados():
    """Renderiza painel de produtos detalhados"""
    if "df_vendas" not in st.session_state or st.session_state["df_vendas"] is None:
        return

    df_vendas = st.session_state["df_vendas"]

    if df_vendas.empty:
        st.info("Nenhum dado disponível para produtos")
        return

    st.subheader("📦 Produtos Detalhados")

    try:
        loading = LoadingHelper.show_loading("Carregando produtos...")

        # Verificar se há IDs de vendas filtradas na grid AgGrid
        ids_vendas_grid_filtradas = st.session_state.get("ids_vendas_grid_filtradas")

        # Determinar quais IDs de vendas usar
        if ids_vendas_grid_filtradas is not None and len(ids_vendas_grid_filtradas) > 0:
            # Usuário filtrou na grid AgGrid - usar IDs filtrados da grid
            venda_ids = ids_vendas_grid_filtradas
        else:
            # Usar TODOS os IDs do df_vendas (que já está filtrado pelos filtros principais)
            if "Id" in df_vendas.columns:
                venda_ids = df_vendas["Id"].tolist()
            elif "ID_Gestao" in df_vendas.columns:
                venda_ids = df_vendas["ID_Gestao"].tolist()
            else:
                venda_ids = None

        # Buscar produtos usando IDs de vendas
        df_produtos = vendas_service.get_produtos_agregados(
            venda_ids=venda_ids,
        )

        LoadingHelper.hide_loading(loading)

        if df_produtos.empty:
            st.info("Nenhum produto encontrado para os filtros aplicados")
            return

        # Preparar dados para exibição
        df_display = df_produtos.copy()

        # Renomear colunas para exibição
        column_mapping = {
            "Nome": "Produto",
            "CodigoExpedicao": "Código Expedição",
            "TotalQuantidade": "Quantidade",
            "TotalValorCusto": "Valor Custo",
            "TotalValorVenda": "Valor Venda",
            "TotalValorDesconto": "Valor Desconto",
            "TotalValorTotal": "Valor Total",
        }

        # Aplicar renomeação apenas para colunas existentes
        existing_columns = {
            k: v for k, v in column_mapping.items() if k in df_display.columns
        }
        df_display = df_display.rename(columns=existing_columns)

        # Garantir que valores monetários sejam float (sem formatação - a grid do AgGrid fará a formatação visual)
        valor_columns = ["Valor Custo", "Valor Venda", "Valor Desconto", "Valor Total"]
        for col in valor_columns:
            if col in df_display.columns:
                df_display[col] = pd.to_numeric(
                    df_display[col], errors="coerce"
                ).fillna(0)

        # Garantir que quantidade seja float (sem formatação - a grid do AgGrid fará a formatação visual)
        if "Quantidade" in df_display.columns:
            df_display["Quantidade"] = pd.to_numeric(
                df_display["Quantidade"], errors="coerce"
            ).fillna(0)

        # Renderizar grid avançada com AgGrid
        df_final = _render_advanced_products_grid(df_display)

    except Exception as e:
        logger.error(f"Erro ao renderizar produtos detalhados: {str(e)}")
        st.error(f"Erro ao carregar produtos: {str(e)}")


def main():
    """
    Função principal do aplicativo
    """
    # Verificar se existem as variáveis de sessão necessárias
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "current_module" not in st.session_state:
        st.session_state.current_module = None

    # Redirecionar para a tela de login se não estiver logado
    if not st.session_state.logged_in:
        login_screen(user_service)
    else:
        selected_module = menu()

        if selected_module:
            st.session_state.current_module = selected_module

        # Redirecionar para o módulo selecionado
        if st.session_state.current_module == "Estoque":
            estoque_main(key="estoque")
        elif st.session_state.current_module == "Cobrança":
            boletos_main(key="boletos")
        elif st.session_state.current_module == "Financeiro":
            extratos_main(key="extratos")
        elif st.session_state.current_module == "Relatório de Vendas":
            if VENDAS_REFATORADO_AVAILABLE:
                vendas_dashboard()  # Versão de produção com cards visuais
            else:
                vendas_main(key="vendas")
        elif st.session_state.current_module == "Relatório de Recebimentos":
            recebimentos_main(key="recebimentos")
        elif st.session_state.current_module == "Relatório de Clientes":
            clientes_main(key="clientes")
        elif st.session_state.current_module == "Comex Produtos":
            comex_main(key="comex")
        elif st.session_state.current_module == "Relatório de Pedidos":
            pedidos_main(key="pedidos")
        elif st.session_state.current_module == "Ordem de Serviço":
            sac_main(key="sac")


if __name__ == "__main__":
    main()
