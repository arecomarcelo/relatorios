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
