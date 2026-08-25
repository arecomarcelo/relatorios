"""
Relatórios - Módulo Vendas - Dashboard de Campanhas
Exibe o desempenho das campanhas de marketing (Google Ads) a partir do
arquivo de origem "Performance da campanha.xlsx"
"""

import logging
import os
import traceback
from datetime import datetime

import pandas as pd
import streamlit as st

# Imports da aplicação
try:
    from presentation.styles.theme_simple import apply_theme
except ImportError as e:
    st.error(f"❌ Erro crítico de importação: {e}")
    st.stop()


# Caminho do arquivo de origem — configurável via variável de ambiente
# CAMPANHAS_XLSX_PATH (.env); mantém o caminho atual como padrão
CAMINHO_XLSX = os.environ.get(
    "CAMPANHAS_XLSX_PATH",
    "/media/areco/Backup/Oficial/Ricardo/Performance da campanha.xlsx",
)

# Colunas exibidas, na ordem solicitada
COLUNAS_EXIBIR = [
    "Campanha",
    "Tipo de campanha",
    "Cliques",
    "Impr.",
    "CTR",
    "CPC méd.",
    "Custo",
    "% de impr. (1ª posição)",
    "% de impr. (parte sup.)",
    "Conversões",
    "Custo / conv.",
    "Taxa de conv.",
]


def _fmt_num(valor, casas: int = 0) -> str:
    """Formata número no padrão brasileiro (1.234,56)"""
    if valor is None or pd.isna(valor):
        return "N/A"
    return f"{valor:,.{casas}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def _fmt_moeda(valor) -> str:
    """Formata valor monetário em Real (R$ 1.234,56)"""
    if valor is None or pd.isna(valor):
        return "N/A"
    return f"R$ {_fmt_num(valor, 2)}"


def _fmt_pct(valor) -> str:
    """Formata fração (0.2060) como percentual (20,60%)"""
    if valor is None or pd.isna(valor):
        return "N/A"
    return f"{_fmt_num(valor * 100, 2)}%"


class CampanhasController:
    """Controller do Dashboard de Campanhas (fonte de dados: arquivo .xlsx)"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def render_dashboard(self):
        """Renderiza o dashboard de Campanhas"""
        try:
            apply_theme()

            st.markdown(
                "<h1 style='text-align: center; color: #1E88E5;'>📊 Relatórios - Dashboard de Campanhas</h1>",
                unsafe_allow_html=True,
            )
            st.markdown("---")

            df, periodo = self._carregar_dados()

            self._render_update_info(periodo)

            if df is None:
                return

            self._render_campanhas(df)

        except Exception as e:
            self.logger.error(f"Erro no dashboard de Campanhas: {str(e)}")
            self.logger.error(traceback.format_exc())
            st.error("❌ Erro inesperado no dashboard. Verifique os logs.")
            with st.expander(
                "🔍 Detalhes do erro (clique para expandir)", expanded=True
            ):
                st.code(traceback.format_exc())
                st.error(f"Tipo de erro: {type(e).__name__}")
                st.error(f"Mensagem: {str(e)}")

    def _carregar_dados(self):
        """Carrega e valida os dados do arquivo de origem. Retorna (df, periodo)"""
        try:
            if not os.path.exists(CAMINHO_XLSX):
                st.error(f"❌ Arquivo de origem não encontrado: `{CAMINHO_XLSX}`")
                return None, None

            with st.spinner("Carregando dados de Campanhas..."):
                # Linha 2 (0-based) traz o período do relatório, ex.:
                # "1 de agosto de 2026 - 25 de agosto de 2026"
                cabecalho = pd.read_excel(CAMINHO_XLSX, header=None, nrows=2)
                periodo = (
                    str(cabecalho.iloc[1, 0]).strip()
                    if len(cabecalho) > 1 and pd.notna(cabecalho.iloc[1, 0])
                    else "N/A"
                )

                df = pd.read_excel(CAMINHO_XLSX, header=2)

            colunas_faltantes = [c for c in COLUNAS_EXIBIR if c not in df.columns]
            if colunas_faltantes:
                st.error(
                    "❌ Colunas ausentes no arquivo de origem: "
                    f"{', '.join(colunas_faltantes)}"
                )
                return None, None

            # Remove linhas de total/rodapé (sem nome de campanha)
            df = df.dropna(subset=["Campanha"]).reset_index(drop=True)

            return df[COLUNAS_EXIBIR], periodo

        except Exception as e:
            self.logger.error(f"Erro ao carregar arquivo de Campanhas: {str(e)}")
            st.error(f"❌ Erro ao ler o arquivo de Campanhas: {str(e)}")
            return None, None

    def _render_update_info(self, periodo):
        """Renderiza informações de atualização (Data/Hora do arquivo + Período)"""
        try:
            with st.expander("🔄 Informações de Atualização", expanded=False):
                if os.path.exists(CAMINHO_XLSX):
                    mtime = datetime.fromtimestamp(os.path.getmtime(CAMINHO_XLSX))
                    data_str = mtime.strftime("%d/%m/%Y")
                    hora_str = mtime.strftime("%H:%M:%S")
                else:
                    data_str, hora_str = "N/A", "N/A"

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📅 Data", data_str)
                with col2:
                    st.metric("⏰ Hora", hora_str)
                with col3:
                    st.metric("📆 Período", periodo or "N/A")

        except Exception as e:
            self.logger.warning(
                f"Erro ao carregar informações de atualização: {str(e)}"
            )

    def _render_campanhas(self, df: pd.DataFrame):
        """Renderiza o grid de Cards de Campanhas — 3 cards por linha"""
        st.subheader(f"📣 Campanhas ({len(df)})")

        if df.empty:
            st.info("ℹ️ Nenhuma campanha encontrada no arquivo de origem.")
            return

        linhas = list(df.iterrows())
        for inicio in range(0, len(linhas), 3):
            grupo = linhas[inicio : inicio + 3]
            colunas = st.columns(3)
            for coluna, (_, row) in zip(colunas, grupo):
                with coluna:
                    st.markdown(self._build_card_campanha(row), unsafe_allow_html=True)

    def _section_label(self, texto: str) -> str:
        """Rótulo de seção dentro do Card — pequeno, maiúsculo, espaçado"""
        return (
            "<div style='font-size:0.6rem; font-weight:700; color:#94a3b8; "
            "text-transform:uppercase; letter-spacing:0.06em; "
            "margin:10px 0 5px;'>"
            f"{texto}"
            "</div>"
        )

    def _stat_tile(self, label: str, valor: str) -> str:
        """Uma métrica isolada, no padrão rótulo (em cima) / valor (embaixo)"""
        return (
            "<div>"
            "<div style='font-size:0.62rem; color:#94a3b8; line-height:1.3;'>"
            f"{label}</div>"
            "<div style='font-size:0.86rem; font-weight:700; color:#1E293B; "
            f"line-height:1.3;'>{valor}</div>"
            "</div>"
        )

    def _grid(self, tiles: list, colunas: int) -> str:
        """Organiza uma lista de tiles em um grid CSS com N colunas"""
        return (
            f"<div style='display:grid; grid-template-columns:repeat({colunas}, 1fr); "
            "gap:8px 6px;'>" + "".join(tiles) + "</div>"
        )

    def _build_card_campanha(self, row: pd.Series) -> str:
        """Monta o HTML de um Card elegante, com métricas agrupadas por seção"""
        nome = str(row["Campanha"]).strip()
        tipo = str(row["Tipo de campanha"]).strip()

        bloco_desempenho = self._grid(
            [
                self._stat_tile("Cliques", _fmt_num(row["Cliques"])),
                self._stat_tile("Impressões", _fmt_num(row["Impr."])),
                self._stat_tile("CTR", _fmt_pct(row["CTR"])),
            ],
            colunas=3,
        )

        bloco_custo = self._grid(
            [
                self._stat_tile("CPC Médio", _fmt_moeda(row["CPC méd."])),
                self._stat_tile("Custo", _fmt_moeda(row["Custo"])),
                self._stat_tile("Custo / Conv.", _fmt_moeda(row["Custo / conv."])),
            ],
            colunas=3,
        )

        bloco_conversao = self._grid(
            [
                self._stat_tile("Conversões", _fmt_num(row["Conversões"], 2)),
                self._stat_tile("Taxa de Conversão", _fmt_pct(row["Taxa de conv."])),
            ],
            colunas=2,
        )

        pct_1a_posicao = _fmt_pct(row["% de impr. (1ª posição)"])
        pct_parte_sup = _fmt_pct(row["% de impr. (parte sup.)"])

        return f"""
        <div style='
            background:#ffffff;
            border-radius:16px;
            box-shadow:0 6px 18px rgba(30, 136, 229, 0.15);
            font-family:Roboto, sans-serif;
            margin-bottom:18px;
            overflow:hidden;
        '>
            <div style='height:4px; background:linear-gradient(90deg, #1E88E5, #64B5F6);'></div>
            <div style='padding:14px 16px 16px;'>
                <div style='min-height:2.5em; text-align:center; font-size:0.86rem; font-weight:700; color:#1E293B; line-height:1.3;'>
                    📣 {nome}
                </div>
                <div style='text-align:center; margin-top:4px;'>
                    <span style='
                        display:inline-block; padding:2px 9px;
                        background:rgba(30, 136, 229, 0.1); color:#1E88E5;
                        border-radius:999px; font-size:0.62rem; font-weight:600;
                    '>{tipo}</span>
                </div>

                {self._section_label("Desempenho")}
                {bloco_desempenho}

                {self._section_label("Custo")}
                {bloco_custo}

                {self._section_label("% Impressão")}
                <div style='background:#f4f8fd; border-radius:10px; padding:8px 10px;'>
                    <div style='display:flex; justify-content:space-between; font-size:0.62rem; color:#64748b;'>
                        <span>🥇 1ª posição</span><span>⬆️ Parte Superior</span>
                    </div>
                    <div style='display:flex; justify-content:space-between; font-size:0.88rem; font-weight:700; color:#1E88E5; margin-top:2px;'>
                        <span>{pct_1a_posicao}</span><span>{pct_parte_sup}</span>
                    </div>
                </div>

                {self._section_label("Conversão")}
                {bloco_conversao}
            </div>
        </div>
        """


def main(key=None):
    """
    Função principal do módulo de Campanhas (compatível com app.py)

    Args:
        key: Chave única para o módulo (requerido pela aplicação principal)
    """
    try:
        controller = CampanhasController()
        controller.render_dashboard()
    except Exception as e:
        st.error("❌ Erro fatal no módulo de Campanhas")
        st.error(str(e))
        logging.error(f"Erro fatal no módulo de Campanhas: {str(e)}")


# Para execução direta (desenvolvimento)
if __name__ == "__main__":
    main()
