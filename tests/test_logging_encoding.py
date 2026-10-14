"""
Regressão do UnicodeEncodeError ('ascii' codec) visto em produção.

O app.py roda django.setup() a cada rerun do Streamlit, o que reaplica
settings.LOGGING. Se o processo estiver com LC_ALL="C" (fallback de locale
quando pt_BR.UTF-8 não existe no container), um FileHandler sem encoding
explícito abre o arquivo em ASCII e falha ao gravar "✓" e acentos.
"""

import copy
import locale
import logging
import logging.config

import pytest

from app import settings


@pytest.fixture
def locale_c():
    original = locale.setlocale(locale.LC_ALL)
    locale.setlocale(locale.LC_ALL, "C")
    yield
    locale.setlocale(locale.LC_ALL, original)


@pytest.fixture
def root_logger_isolado():
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield root
    for handler in root.handlers:
        if handler not in handlers:
            handler.close()
    root.handlers[:] = handlers
    root.setLevel(level)


def test_logging_do_django_grava_unicode_com_locale_c(
    tmp_path, locale_c, root_logger_isolado
):
    arquivo = tmp_path / "relatorios.log"
    config = copy.deepcopy(settings.LOGGING)
    config["handlers"]["file"]["filename"] = arquivo

    logging.config.dictConfig(config)
    logging.getLogger("teste.encoding").info("✓ VendasService inicializado — ação")
    for handler in root_logger_isolado.handlers:
        handler.flush()

    assert "✓ VendasService inicializado — ação" in arquivo.read_text(encoding="utf-8")


def test_logging_do_django_rotaciona_o_arquivo(tmp_path, root_logger_isolado):
    # O relatorios.log fica dentro do container e chegou a ~20 MB sem rotação
    # (auditoria Hostinger, 06/10/2026): o handler precisa ter teto de tamanho.
    arquivo = tmp_path / "relatorios.log"
    config = copy.deepcopy(settings.LOGGING)
    config["handlers"]["file"]["filename"] = arquivo
    config["handlers"]["file"]["maxBytes"] = 1024

    logging.config.dictConfig(config)
    logger = logging.getLogger("teste.rotacao")
    for numero in range(100):
        logger.info("linha %03d ✓ com acentuação para encher o arquivo", numero)
    for handler in root_logger_isolado.handlers:
        handler.flush()

    assert arquivo.stat().st_size <= 1024
    assert (tmp_path / "relatorios.log.1").exists()
    assert (
        len(list(tmp_path.glob("relatorios.log.*")))
        <= settings.LOGGING["handlers"]["file"]["backupCount"]
    )
