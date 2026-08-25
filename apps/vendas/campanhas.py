"""
Relatórios - Módulo Vendas - Dashboard de Campanhas
Exibe o desempenho das campanhas de marketing (Google Ads) a partir do
arquivo de origem "documentacao/Relatorio Adwords.xlsx"
"""

import io
import logging
import os
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# Imports da aplicação
try:
    from presentation.styles.theme_simple import apply_theme
except ImportError as e:
    st.error(f"❌ Erro crítico de importação: {e}")
    st.stop()


# Caminho do arquivo de origem — resolvido em 3 níveis (do mais para o menos
# prioritário): 1) variável de ambiente CAMPANHAS_XLSX_PATH (override manual);
# 2) arquivo "vivo" em data/ (volume gravável, persiste entre deploys — é
# onde o botão de upload da tela grava); 3) arquivo semente versionado em
# documentacao/ (acompanha o git/imagem Docker, usado só até o primeiro
# upload acontecer). Resolvido a cada leitura (não é uma constante fixa),
# pois o arquivo em data/ pode passar a existir em tempo de execução.
_PROJETO_DIR = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJETO_DIR / "data"
_ARQUIVO_LIVE = _DATA_DIR / "Relatorio Adwords.xlsx"
_ARQUIVO_SEED = _PROJETO_DIR / "documentacao" / "Relatorio Adwords.xlsx"


def _resolver_caminho_xlsx() -> Path:
    """Resolve o caminho do arquivo de origem no momento da leitura"""
    override = os.environ.get("CAMPANHAS_XLSX_PATH")
    if override:
        return Path(override)
    if _ARQUIVO_LIVE.exists():
        return _ARQUIVO_LIVE
    return _ARQUIVO_SEED


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
            self._render_upload_arquivo()

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
            caminho = _resolver_caminho_xlsx()
            if not caminho.exists():
                st.error(f"❌ Arquivo de origem não encontrado: `{caminho}`")
                return None, None

            with st.spinner("Carregando dados de Campanhas..."):
                # Linha 2 (0-based) traz o período do relatório, ex.:
                # "1 de agosto de 2026 - 25 de agosto de 2026"
                cabecalho = pd.read_excel(caminho, header=None, nrows=2)
                periodo = (
                    str(cabecalho.iloc[1, 0]).strip()
                    if len(cabecalho) > 1 and pd.notna(cabecalho.iloc[1, 0])
                    else "N/A"
                )

                df = pd.read_excel(caminho, header=2)

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
                caminho = _resolver_caminho_xlsx()
                if caminho.exists():
                    mtime = datetime.fromtimestamp(caminho.stat().st_mtime)
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

    def _usuario_pode_atualizar(self) -> bool:
        """Só admin (bypass) ou quem tiver a permissão change_campanhas"""
        username = st.session_state.get("username")
        if username == "admin":
            return True
        permissions = st.session_state.get("permissions", []) or []
        return "change_campanhas" in permissions

    def _render_upload_arquivo(self):
        """Botão de atualização do arquivo de origem — só para quem tem permissão"""
        if not self._usuario_pode_atualizar():
            return

        with st.expander("📤 Atualizar Arquivo de Origem", expanded=False):
            st.caption(
                "Envie o novo export de Performance de Campanhas (.xlsx) "
                "do Google Ads. O arquivo atual será substituído."
            )
            arquivo_enviado = st.file_uploader(
                "Arquivo .xlsx",
                type=["xlsx"],
                key="campanhas_upload_arquivo",
                label_visibility="collapsed",
            )
            if arquivo_enviado is not None:
                if st.button(
                    "✅ Confirmar Atualização",
                    type="primary",
                    key="btn_confirmar_upload_campanhas",
                ):
                    self._salvar_arquivo_enviado(arquivo_enviado)

    def _salvar_arquivo_enviado(self, arquivo_enviado) -> None:
        """Valida e grava o arquivo enviado no volume gravável (data/)"""
        try:
            conteudo = arquivo_enviado.getvalue()

            with st.spinner("Validando arquivo..."):
                try:
                    df_teste = pd.read_excel(io.BytesIO(conteudo), header=2)
                except Exception as e:
                    st.error(f"❌ Não foi possível ler o arquivo enviado: {str(e)}")
                    return

                colunas_faltantes = [
                    c for c in COLUNAS_EXIBIR if c not in df_teste.columns
                ]
                if colunas_faltantes:
                    st.error(
                        "❌ Arquivo inválido — colunas ausentes: "
                        f"{', '.join(colunas_faltantes)}"
                    )
                    return

            _DATA_DIR.mkdir(parents=True, exist_ok=True)
            # Escrita atômica: grava num arquivo temporário no mesmo diretório
            # e só então substitui o arquivo ativo — evita leituras parciais
            # por outra sessão enquanto o upload está em andamento.
            with tempfile.NamedTemporaryFile(
                dir=_DATA_DIR, delete=False, suffix=".xlsx"
            ) as tmp:
                tmp.write(conteudo)
                tmp_path = tmp.name
            os.replace(tmp_path, _ARQUIVO_LIVE)

            usuario = st.session_state.get("username", "desconhecido")
            self.logger.info(
                f"✓ Arquivo de Campanhas atualizado via upload por '{usuario}'"
            )
            st.success("✅ Arquivo atualizado com sucesso!")
            st.rerun()

        except Exception as e:
            self.logger.error(f"Erro ao salvar arquivo enviado de Campanhas: {str(e)}")
            st.error(f"❌ Erro ao processar o arquivo enviado: {str(e)}")

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

        # Atenção: nenhuma linha em branco dentro deste HTML — uma linha vazia
        # encerra o "bloco HTML bruto" que o parser Markdown do Streamlit
        # reconhece, e o restante passa a ser tratado como texto/código puro
        # em vez de renderizado (bug real já visto: seções apareciam como
        # texto cru na tela). Todo o card precisa ficar como um bloco contínuo.
        pct_box = (
            "<div style='background:#f4f8fd; border-radius:10px; padding:8px 10px;'>"
            "<div style='display:flex; justify-content:space-between; font-size:0.62rem; color:#64748b;'>"
            "<span>🥇 1ª posição</span><span>⬆️ Parte Superior</span>"
            "</div>"
            "<div style='display:flex; justify-content:space-between; font-size:0.88rem; font-weight:700; color:#1E88E5; margin-top:2px;'>"
            f"<span>{pct_1a_posicao}</span><span>{pct_parte_sup}</span>"
            "</div>"
            "</div>"
        )

        return (
            "<div style='background:#ffffff; border-radius:16px; "
            "box-shadow:0 6px 18px rgba(30, 136, 229, 0.15); "
            "font-family:Roboto, sans-serif; margin-bottom:18px; overflow:hidden;'>"
            "<div style='height:4px; background:linear-gradient(90deg, #1E88E5, #64B5F6);'></div>"
            "<div style='padding:14px 16px 16px;'>"
            "<div style='min-height:2.5em; text-align:center; font-size:0.86rem; "
            f"font-weight:700; color:#1E293B; line-height:1.3;'>📣 {nome}</div>"
            "<div style='text-align:center; margin-top:4px;'>"
            "<span style='display:inline-block; padding:2px 9px; "
            "background:rgba(30, 136, 229, 0.1); color:#1E88E5; border-radius:999px; "
            f"font-size:0.62rem; font-weight:600;'>{tipo}</span>"
            "</div>"
            f"{self._section_label('Desempenho')}"
            f"{bloco_desempenho}"
            f"{self._section_label('Custo')}"
            f"{bloco_custo}"
            f"{self._section_label('% Impressão')}"
            f"{pct_box}"
            f"{self._section_label('Conversão')}"
            f"{bloco_conversao}"
            "</div>"
            "</div>"
        )


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
