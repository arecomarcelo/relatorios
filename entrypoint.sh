#!/bin/sh
set -e

# Sem advisory lock/migrate/collectstatic aqui: o SGR não gera migrações
# (modelos já existem no banco `sga`) e não serve o Django admin via HTTP
# neste deploy — Django roda só em processo, para ORM. O retry de conexão
# ao Postgres já é feito em repository.py (_conectar_com_retry), então o
# Streamlit sobe direto.

exec "$@"
