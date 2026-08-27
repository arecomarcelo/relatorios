"""
Acesso de leitura à identidade central do ecossistema oficial (schema
`administracao`, banco `oficial_db`) — usada só para autenticação/permissão
do menu (Fase 4 da migração descrita no plano "Registro do Relatórios na
identidade central", 27/08/2026).

Conexão DEDICADA, independente da conexão de dados de negócio de
`service.py::DataService` (que segue apontando para onde a migração de dados
de negócio deixar configurado) — evita acoplar esta mudança de
identidade/permissão à outra frente que cuida dos dados.

O Relatórios não tem schema próprio no `oficial_db` (não é dono de nenhuma
tabela) — só enxerga as 5 tabelas do schema `administracao` liberadas por
GRANT SELECT ao usuário `relatorios_user` (ver `administracao/apps/
administracao/provisionamento.py`), por isso as queries aqui sempre
qualificam o schema explicitamente.
"""

from typing import Any, Dict, Optional, Set, Tuple, cast

from psycopg2 import sql

from repository import _conectar_com_retry
from service import _get_db_secret


def _build_central_db_config() -> Dict[str, Any]:
    return {
        "dbname": _get_db_secret("OFICIAL_DB_NAME", "oficial_db"),
        "user": _get_db_secret("OFICIAL_DB_USER", "relatorios_user"),
        "password": _get_db_secret("OFICIAL_DB_PASSWORD"),
        "host": _get_db_secret("OFICIAL_DB_HOST", "localhost"),
        "port": _get_db_secret("OFICIAL_DB_PORT", "5440"),
    }


class CentralAuthRepository:
    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        self.db_config = db_config or _build_central_db_config()

    def connect(self):
        return _conectar_com_retry(self.db_config)

    def get_central_user(self, username: str) -> Optional[Tuple]:
        """Retorna (id, password, is_active, is_superuser) de
        administracao.auth_user, ou None se o username não existir."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                sql.SQL(
                    """
                    SELECT id, password, is_active, is_superuser
                    FROM administracao.auth_user
                    WHERE username = %s
                    """
                ),
                (username,),
            )
            return cast(Optional[Tuple], cursor.fetchone())
        finally:
            cursor.close()
            conn.close()

    def get_acesso_app(self, app_slug: str, user_id: int) -> Optional[Tuple]:
        """Retorna (acesso_app_id, pode_visualizar, pode_incluir, pode_editar,
        pode_excluir) para o usuário nesta app, ou None se não houver
        AcessoApp concedido (ou a app não estiver registrada)."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                sql.SQL(
                    """
                    SELECT aa.id, aa.pode_visualizar, aa.pode_incluir,
                           aa.pode_editar, aa.pode_excluir
                    FROM administracao."AcessoApp" aa
                    JOIN administracao."AppRegistrada" ar ON ar.id = aa.app_id
                    WHERE ar.slug = %s AND aa.usuario_id = %s
                    """
                ),
                (app_slug, user_id),
            )
            return cast(Optional[Tuple], cursor.fetchone())
        finally:
            cursor.close()
            conn.close()

    def get_chaves_modulos_visiveis(self, acesso_app_id: int) -> Set[str]:
        """Chaves de ModuloMenu com AcessoModuloMenu explícito para este
        AcessoApp. Conjunto vazio = sem restrição gravada (regra do model:
        vê todos os módulos) — a decisão "vazio == tudo liberado" fica a
        cargo de quem chama, não deste repositório."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                sql.SQL(
                    """
                    SELECT mm.chave
                    FROM administracao."AcessoModuloMenu" amm
                    JOIN administracao."ModuloMenu" mm ON mm.id = amm.modulo_id
                    WHERE amm.acesso_app_id = %s
                    """
                ),
                (acesso_app_id,),
            )
            return {row[0] for row in cursor.fetchall()}
        finally:
            cursor.close()
            conn.close()
