"""Ranking de Vendedores lido do cadastro `vendas."Vendedores"` (03/11/2026).

Quem aparece vem de `ExibirRanking`; a foto vem do banco. Ocultar um vendedor
só tira o card dele — os valores dos demais não mudam.
"""

import importlib.util
from pathlib import Path
from unittest import mock

import pandas as pd
import pytest

# `app` é o pacote Django (app/settings.py); o app.py do Streamlit é carregado
# pelo caminho, como faz scripts/daily_sales_preview.py. Ele também roda o
# django.setup() de que o repositório precisa.
_spec = importlib.util.spec_from_file_location(
    "relatorios_dashboard", Path(__file__).resolve().parent.parent / "app.py"
)
dashboard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dashboard)

from infrastructure.database.repositories_vendas import VendaRepository  # noqa: E402

FOTO_PNG = b"\x89PNG\r\n\x1a\nfake"


def test_repositorio_filtra_exibir_ranking_e_traz_a_foto():
    cursor = mock.MagicMock()
    cursor.fetchall.return_value = [
        ("Rocha Jr.", 224058, "Rocha", 10, memoryview(FOTO_PNG)),
        ("Sem Curto", None, None, None, None),
    ]
    conexao = mock.MagicMock()
    conexao.cursor.return_value.__enter__.return_value = cursor
    with mock.patch("infrastructure.database.repositories_vendas.connection", conexao):
        vendedores = VendaRepository.get_vendedores_ranking(mock.Mock())

    sql = cursor.execute.call_args[0][0]
    assert 'WHERE "ExibirRanking"' in sql
    assert vendedores == [
        {
            "nome": "Rocha Jr.",
            "vendedor_id": 224058,
            "nome_curto": "Rocha",
            "percentual": 10.0,
            "foto": FOTO_PNG,
        },
        {
            "nome": "Sem Curto",
            "vendedor_id": None,
            "nome_curto": "Sem Curto",
            "percentual": 0.0,
            "foto": None,
        },
    ]


def _vendedor(nome, foto=None, percentual=0.0):
    return {
        "nome": nome,
        "vendedor_id": None,
        "nome_curto": nome.split()[0],
        "percentual": percentual,
        "foto": foto,
    }


@pytest.fixture
def ranking():
    """Renderiza o Ranking com banco e Streamlit simulados; devolve os cards."""
    df_vendas = pd.DataFrame(
        {
            "VendedorNome": ["Ana", "Bia", "Bia", "Oculto"],
            "ValorTotal": [100.0, 50.0, 70.0, 999.0],
        }
    )
    cards = []
    estado = {
        "df_vendas": df_vendas,
        "data_inicio_filtro": pd.Timestamp("2026-10-01").date(),
        "data_fim_filtro": pd.Timestamp("2026-10-31").date(),
    }

    def renderizar(vendedores):
        cards.clear()
        with mock.patch.object(
            dashboard.vendas_service.venda_repository,
            "get_vendedores_ranking",
            return_value=vendedores,
        ), mock.patch.object(
            dashboard, "_calcular_vendas_periodo_anterior", return_value={"Ana": 80.0}
        ), mock.patch.object(
            dashboard,
            "_render_card_vendedor",
            side_effect=lambda col, vendedor, fmt: cards.append(vendedor),
        ), mock.patch.object(
            dashboard.st, "session_state", estado
        ), mock.patch.object(
            dashboard.st, "columns", side_effect=lambda n: [mock.MagicMock()] * n
        ), mock.patch.object(
            dashboard.st, "info"
        ) as info:
            total = dashboard._render_vendedores_com_fotos(None)
        return total, cards, info

    return renderizar


def test_so_exibidos_aparecem_e_valores_nao_mudam(ranking):
    total, cards, _ = ranking(
        [_vendedor("Ana", FOTO_PNG, percentual=10.0), _vendedor("Bia")]
    )
    assert total == 2
    assert [c["nome"] for c in cards] == ["Bia", "Ana"]  # 120 > 100
    bia, ana = cards
    assert bia["total_valor"] == 120.0
    assert ana["total_valor"] == 100.0
    assert ana["vendas_ano_anterior"] == 80.0
    assert ana["percentual_meta"] == 10.0
    assert ana["foto_b64"].startswith("data:image/png;base64,")
    assert bia["foto_b64"] is None  # card mostra as iniciais


def test_linhas_de_seis_cards_sem_limite_de_doze(ranking):
    vendedores = [_vendedor(f"Vendedor {i:02d}") for i in range(14)]
    total, cards, _ = ranking(vendedores)
    assert total == 14
    assert len(cards) == 14


def test_ninguem_exibido_mostra_aviso(ranking):
    total, cards, info = ranking([])
    assert total == 0
    assert cards == []
    info.assert_called_once()
