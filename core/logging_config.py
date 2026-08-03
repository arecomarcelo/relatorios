"""
Sistema de Logging Centralizado e Inteligente para Relatórios

Este módulo fornece configuração unificada de logging para toda a aplicação,
com suporte a rotação de arquivos, níveis personalizados e formatação adequada.

Uso básico:
    from core.logging_config import get_logger

    logger = get_logger(__name__)
    logger.info("Mensagem informativa")
    logger.error("Erro encontrado", exc_info=True)
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class RelatoriosLogger:
    """
    Gerenciador centralizado de logging para o Relatórios

    Características:
    - Rotação automática de arquivos (10MB por arquivo, mantém 5 backups)
    - Formatação padronizada com timestamp, nível e contexto
    - Diferentes níveis de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Log em arquivo e console simultaneamente
    - Filtros para evitar logs repetitivos e desnecessários
    """

    _instances: dict[str, logging.Logger] = {}
    _initialized: bool = False

    # Diretório de logs
    LOG_DIR = Path("logs")
    LOG_FILE = LOG_DIR / "relatorios.log"
    ERROR_LOG_FILE = LOG_DIR / "relatorios_errors.log"

    # Configurações de rotação
    MAX_BYTES = 10 * 1024 * 1024  # 10MB por arquivo
    BACKUP_COUNT = 5  # Mantém 5 backups

    # Nível de log padrão
    DEFAULT_LEVEL = logging.INFO

    # Mensagens que devem ser filtradas (evitar repetição)
    FILTERED_MESSAGES = [
        "VendasService criado com sucesso",
        "Container cache cleared",
    ]

    @classmethod
    def setup(cls, level: int = None) -> None:
        """
        Configura o sistema de logging uma única vez

        Args:
            level: Nível de log (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if cls._initialized:
            return

        # Criar diretório de logs se não existir
        cls.LOG_DIR.mkdir(exist_ok=True)

        # Configurar nível
        log_level = level or cls.DEFAULT_LEVEL

        # Remover handlers existentes para evitar duplicação
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(log_level)

        # Formato de log detalhado e informativo
        detailed_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

        # Formato simplificado para console
        console_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'
        )

        # Handler para arquivo principal (com rotação)
        file_handler = logging.handlers.RotatingFileHandler(
            cls.LOG_FILE,
            maxBytes=cls.MAX_BYTES,
            backupCount=cls.BACKUP_COUNT,
            encoding='utf-8',
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)

        # Handler para erros (arquivo separado)
        error_handler = logging.handlers.RotatingFileHandler(
            cls.ERROR_LOG_FILE,
            maxBytes=cls.MAX_BYTES,
            backupCount=cls.BACKUP_COUNT,
            encoding='utf-8',
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)

        # Handler para console (apenas INFO e acima)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)

        # Adicionar filtro para evitar logs repetitivos
        console_handler.addFilter(cls._filter_repetitive_logs)

        # Adicionar handlers ao root logger
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(console_handler)

        cls._initialized = True

        # Log de inicialização
        init_logger = logging.getLogger(__name__)
        init_logger.info("=" * 80)
        init_logger.info(
            f"Sistema de Logging Relatórios iniciado - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )
        init_logger.info(f"Nível: {logging.getLevelName(log_level)}")
        init_logger.info(f"Arquivo principal: {cls.LOG_FILE}")
        init_logger.info(f"Arquivo de erros: {cls.ERROR_LOG_FILE}")
        init_logger.info("=" * 80)

    @staticmethod
    def _filter_repetitive_logs(record: logging.LogRecord) -> bool:
        """
        Filtro para evitar mensagens repetitivas no console

        Args:
            record: Registro de log

        Returns:
            True se a mensagem deve ser exibida, False caso contrário
        """
        # Permitir sempre erros e warnings
        if record.levelno >= logging.WARNING:
            return True

        # Filtrar mensagens repetitivas específicas
        message = record.getMessage()
        for filtered_msg in RelatoriosLogger.FILTERED_MESSAGES:
            if filtered_msg in message:
                return False

        return True

    @classmethod
    def get_logger(cls, name: str, level: Optional[int] = None) -> logging.Logger:
        """
        Obtém um logger configurado para o módulo especificado

        Args:
            name: Nome do módulo (geralmente __name__)
            level: Nível de log opcional (sobrescreve o padrão)

        Returns:
            Logger configurado

        Exemplo:
            logger = RelatoriosLogger.get_logger(__name__)
            logger.info("Operação concluída")
        """
        # Garantir que o sistema está inicializado
        if not cls._initialized:
            cls.setup()

        # Retornar logger existente ou criar novo
        if name not in cls._instances:
            logger: logging.Logger = logging.getLogger(name)
            if level:
                logger.setLevel(level)
            cls._instances[name] = logger

        return cls._instances[name]


# Função de conveniência para uso direto
def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Função de conveniência para obter um logger configurado

    Args:
        name: Nome do módulo (geralmente __name__)
        level: Nível de log opcional

    Returns:
        Logger configurado

    Exemplo:
        from core.logging_config import get_logger

        logger = get_logger(__name__)
        logger.info("Aplicação iniciada")
        logger.warning("Atenção: configuração não encontrada")
        logger.error("Erro ao processar dados", exc_info=True)
    """
    return RelatoriosLogger.get_logger(name, level)


# Funções auxiliares para logging contextual
def log_function_call(logger: logging.Logger):
    """
    Decorator para logar entrada e saída de funções

    Uso:
        @log_function_call(logger)
        def minha_funcao(param1, param2):
            return resultado
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"→ Chamando {func.__name__} com args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"← {func.__name__} retornou com sucesso")
                return result
            except Exception as e:
                logger.error(f"✗ {func.__name__} falhou: {e}", exc_info=True)
                raise

        return wrapper

    return decorator


def log_operation(logger: logging.Logger, operation: str, details: str = ""):
    """
    Context manager para logar operações com tempo de execução

    Uso:
        with log_operation(logger, "Buscar vendas", "Período: 01/12 a 31/12"):
            vendas = buscar_vendas()
    """

    class OperationLogger:
        def __enter__(self):
            self.start_time = datetime.now()
            msg = f"▶ Iniciando: {operation}"
            if details:
                msg += f" ({details})"
            logger.info(msg)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = (datetime.now() - self.start_time).total_seconds()
            if exc_type:
                logger.error(
                    f"✗ Falha em: {operation} | Duração: {duration:.2f}s", exc_info=True
                )
            else:
                logger.info(f"✓ Concluído: {operation} | Duração: {duration:.2f}s")
            return False

    return OperationLogger()


# Configurar automaticamente ao importar
RelatoriosLogger.setup()
