"""
Repositórios específicos para Recebimentos usando Django ORM com SQL bruto
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from django.db import connection

import pandas as pd

from core.exceptions import DatabaseError
from infrastructure.database.base import BaseRepository

logger = logging.getLogger(__name__)


class RecebimentosRepository(BaseRepository):
    """Repositório para operações com recebimentos usando SQL bruto via Django"""

    def get_recebimentos_filtrados(
        self,
        data_inicial: date,
        data_final: date,
    ) -> pd.DataFrame:
        """
        Obtém recebimentos com filtros aplicados usando SQL bruto

        Args:
            data_inicial: Data inicial do filtro
            data_final: Data final do filtro

        Returns:
            DataFrame com os dados de recebimentos

        Raises:
            DatabaseError: Se houver erro na consulta
        """
        try:
            # Query ajustada para garantir filtragem correta por data
            query = """
                SELECT
                    DATE(vp."DataVencimento") as "Vencimento",
                    vp."Valor",
                    vp."NomeFormaPagamento" as "FormaPagamento",
                    v."ClienteNome" as "Cliente"
                FROM vendas."VendaPagamentos" vp
                INNER JOIN vendas."Vendas" v ON v."ID_Gestao" = vp."Venda_ID"
                WHERE vp."NomeFormaPagamento" IN (SELECT "NomeFormaPagamento" FROM vendas."VendaFormaPagamento")
                  AND DATE(vp."DataVencimento") >= %s
                  AND DATE(vp."DataVencimento") <= %s
                ORDER BY DATE(vp."DataVencimento"), v."ClienteNome"
            """

            params: List[Any] = [data_inicial, data_final]

            logger.info(
                f"Executando query com parâmetros: data_inicial={data_inicial}, data_final={data_final}"
            )

            with connection.cursor() as cursor:
                cursor.execute(query, params)
                columns = [col[0] for col in cursor.description]
                data = cursor.fetchall()

                result = pd.DataFrame(data, columns=columns)

            logger.info(f"Retrieved {len(result)} recebimentos records")

            # Log das datas retornadas para debug
            if not result.empty and "Vencimento" in result.columns:
                datas_unicas = result["Vencimento"].unique()
                logger.info(f"Datas únicas retornadas pela query: {datas_unicas}")

            return result

        except Exception as e:
            logger.error(f"Error fetching recebimentos: {str(e)}")
            raise DatabaseError(f"Erro ao buscar recebimentos: {str(e)}")
