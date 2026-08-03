import time
from typing import Any, Dict, List, Optional, Tuple, cast

import pandas as pd
import psycopg2
import psycopg2.extensions
from psycopg2 import sql
from sqlalchemy import create_engine

from core.logging_config import get_logger

logger = get_logger(__name__)

CONNECT_TIMEOUT = 5  # segundos até desistir de uma tentativa de conexão TCP
MAX_TENTATIVAS = 3
ESPERA_ENTRE_TENTATIVAS = 2  # segundos


def _conectar_com_retry(db_config: Dict[str, Any]) -> psycopg2.extensions.connection:
    """Conecta ao Postgres com timeout curto e retry para absorver falhas
    intermitentes de rede entre o host da app e o servidor de banco."""
    ultimo_erro: Optional[Exception] = None
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            return psycopg2.connect(connect_timeout=CONNECT_TIMEOUT, **db_config)
        except Exception as e:
            ultimo_erro = e
            logger.warning(
                f"Falha ao conectar ao banco (tentativa {tentativa}/{MAX_TENTATIVAS}): {e}"
            )
            if tentativa < MAX_TENTATIVAS:
                time.sleep(ESPERA_ENTRE_TENTATIVAS)
    raise Exception(
        f"Erro ao conectar ao banco de dados após {MAX_TENTATIVAS} tentativas: {ultimo_erro}"
    )


class UserRepository:
    def __init__(self, db_config):
        self.db_config = db_config

    def connect(self):
        return _conectar_com_retry(self.db_config)

    def get_user(self, username):
        conn = self.connect()
        try:
            cursor = conn.cursor()
            query = sql.SQL("SELECT * FROM auth_user WHERE username = %s")
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            return user
        finally:
            cursor.close()
            conn.close()

    def get_user_permissions(self, user_id):
        conn = self.connect()
        try:
            cursor = conn.cursor()
            query = sql.SQL(
                """
                SELECT permission.codename
                FROM auth_user_groups AS ug
                JOIN auth_group_permissions AS gp ON ug.group_id = gp.group_id
                JOIN auth_permission AS permission ON gp.permission_id = permission.id
                WHERE ug.user_id = %s

                UNION

                SELECT permission.codename
                FROM auth_user_user_permissions AS up
                JOIN auth_permission AS permission ON up.permission_id = permission.id
                WHERE up.user_id = %s
            """
            )
            cursor.execute(query, (user_id, user_id))
            permissions = cursor.fetchall()
            return [
                perm[0] for perm in permissions
            ]  # Retornar apenas os nomes das permissões
        finally:
            cursor.close()
            conn.close()


class DatabaseRepository:
    def __init__(self, db_config):
        self.db_config = db_config
        self.engine = self.create_connection()

    def create_connection(self):
        try:
            # Usando o SQLAlchemy para criar a engine
            engine = create_engine(
                f'postgresql://{self.db_config["user"]}:{self.db_config["password"]}@'
                f'{self.db_config["host"]}/{self.db_config["dbname"]}',
                connect_args={"connect_timeout": CONNECT_TIMEOUT},
            )
            return engine
        except Exception as e:
            raise Exception(f"Erro ao conectar ao banco de dados: {e}")

    def fetch_data(self, table_name, campos):
        try:
            # Formatar os campos para a consulta SQL
            campos_formatados = ", ".join(
                [f'"{campo}"' for campo in campos]
            )  # Usar aspas duplas
            query = f'SELECT {campos_formatados} FROM "{table_name}";'
            return pd.read_sql(query, self.engine)
        except Exception as e:
            raise Exception(f"Erro ao buscar dados da tabela {table_name}: {e}")


class ExtratoRepository:
    def __init__(self, db_config):
        self.db_config = db_config

    def connect(self):
        return _conectar_com_retry(self.db_config)

    def get_extratos_filtrados(
        self, data_inicial, data_final, empresas=None, centros_custo=None
    ):
        conn = self.connect()
        try:
            # data_inicial += ' 00:00:00'
            # data_final += ' 23:59:59'

            cursor = conn.cursor()
            query = sql.SQL(
                """
                SELECT b.descricao AS Banco, e.agencia, e.conta_corrente, e."data", 
                       e.documento, e.historico_descricao AS Descricao, e.valor, 
                       e.debito_credito AS "D/C", em.nome AS Empresa, 
                       cc.descricao AS CentroCusto
                FROM "Extratos" e 
                INNER JOIN "Bancos" b ON b.id = e.banco_id 
                LEFT JOIN "Empresas" em ON em.id = e.empresa_id
                LEFT JOIN "CentroCustos" cc ON cc.id = e.centrocusto_id
                WHERE e."data" BETWEEN %s AND %s
            """
            )

            params = [data_inicial, data_final]
            if empresas:
                query += sql.SQL(" AND em.nome IN %s")
                params.append(tuple(empresas))
            if centros_custo:
                query += sql.SQL(" AND cc.descricao IN %s")
                params.append(tuple(centros_custo))

            cursor.execute(query, params)
            extratos = cursor.fetchall()

            # Obter os nomes das colunas
            colunas = [desc[0] for desc in cursor.description]

            # Retornar um DataFrame
            return pd.DataFrame(extratos, columns=colunas)
        finally:
            cursor.close()
            conn.close()


class BoletoRepository:
    def __init__(self, db_config):
        self.db_config = db_config

    def connect(self):
        return _conectar_com_retry(self.db_config)

    def get_boletos_filtrados(self, data_inicial, data_final):
        conn = self.connect()
        try:
            data_inicial += " 00:00:00"
            data_final += " 23:59:59"

            cursor = conn.cursor()
            query = sql.SQL(
                """
                select "Nome", "Boleto", "Vencimento", "DataHoraEnvio" as Envio, "Status" 
                from "BoletosEnviados"
                WHERE "DataHoraEnvio" BETWEEN %s AND %s                            
            """
            )

            params = [data_inicial, data_final]

            cursor.execute(query, params)
            extratos = cursor.fetchall()

            # Obter os nomes das colunas
            colunas = [desc[0] for desc in cursor.description]

            # Retornar um DataFrame
            return pd.DataFrame(extratos, columns=colunas)
        finally:
            cursor.close()
            conn.close()


class ClienteRepository:
    def __init__(self, db_config: Dict[str, Any]) -> None:
        self.db_config = db_config

    def connect(self) -> psycopg2.extensions.connection:
        """Establish database connection"""
        return cast(psycopg2.extensions.connection, _conectar_com_retry(self.db_config))

    def get_clientes(self) -> pd.DataFrame:
        """Get all client data"""
        conn = self.connect()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT "TipoPessoa", 
                           COALESCE(NULLIF("RazaoSocial", ''), '-') AS "RazaoSocial", 
                           "Nome", "CNPJ", "CPF", "Email"
                    FROM "Clientes"
                    ORDER BY "RazaoSocial"
                """
                )
                clientes = cursor.fetchall()
                colunas = [desc[0] for desc in cursor.description]
                return pd.DataFrame(clientes, columns=colunas)
        finally:
            conn.close()
