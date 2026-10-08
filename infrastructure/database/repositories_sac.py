"""
Repositórios específicos para SAC usando Django ORM com SQL bruto
"""

import logging
from typing import Any, Dict

from django.db import connection

import pandas as pd

from core.exceptions import DatabaseError
from infrastructure.database.base import BaseRepository

logger = logging.getLogger(__name__)


class SacAtualizacaoRepository(BaseRepository):
    """Repositório para informações de atualização do SAC"""

    def get_ultima_atualizacao(self) -> pd.DataFrame:
        """Obtém informações da última atualização do RPA de SAC (RPA_id = 9)"""
        try:
            # Última atualização no controle oficial (rpa."ControleAtualizacao")
            # filtrada pelo RPA de SAC (RPA_id = 9)
            query = '''
                SELECT
                    TO_CHAR(fim AT TIME ZONE 'America/Sao_Paulo', 'DD/MM/YYYY') AS "Data",
                    TO_CHAR(fim AT TIME ZONE 'America/Sao_Paulo', 'HH24:MI') AS "Hora",
                    periodo AS "Periodo",
                    inseridos::text AS "Inseridos",
                    atualizados::text AS "Atualizados"
                FROM rpa."ControleAtualizacao"
                WHERE rpa_id = 9
                ORDER BY fim DESC
                LIMIT 1
            '''

            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                data = cursor.fetchall()

                result = pd.DataFrame(data, columns=columns)

            return result

        except Exception as e:
            logger.error(f"Error fetching last update info: {str(e)}")
            raise DatabaseError(f"Erro ao buscar informações de atualização: {str(e)}")

    def get_historico_atualizacoes(self, limite: int = 10) -> pd.DataFrame:
        """Obtém histórico de atualizações do RPA de SAC (RPA_id = 9)"""
        try:
            # Histórico de atualizações no controle oficial (rpa."ControleAtualizacao")
            # filtrada pelo RPA de SAC (RPA_id = 9)
            query = '''
                SELECT
                    TO_CHAR(fim AT TIME ZONE 'America/Sao_Paulo', 'DD/MM/YYYY') AS "Data",
                    TO_CHAR(fim AT TIME ZONE 'America/Sao_Paulo', 'HH24:MI') AS "Hora",
                    periodo AS "Periodo",
                    inseridos::text AS "Inseridos",
                    atualizados::text AS "Atualizados"
                FROM rpa."ControleAtualizacao"
                WHERE rpa_id = 9
                ORDER BY fim DESC
                LIMIT %s
            '''

            with connection.cursor() as cursor:
                cursor.execute(query, [limite])
                columns = [col[0] for col in cursor.description]
                data = cursor.fetchall()

                result = pd.DataFrame(data, columns=columns)

            return result

        except Exception as e:
            logger.error(f"Error fetching update history: {str(e)}")
            raise DatabaseError(f"Erro ao buscar histórico de atualizações: {str(e)}")

    def health_check(self) -> bool:
        """Verifica se a conexão está saudável"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False
