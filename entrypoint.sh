#!/bin/sh
set -e

# Sem advisory lock/migrate/collectstatic aqui: o Relatórios não gera migrações
# (modelos managed=False sobre os schemas das apps donas no `oficial_db`) e não serve o Django admin via HTTP
# neste deploy — Django roda só em processo, para ORM. O retry de conexão
# ao Postgres já é feito em repository.py (_conectar_com_retry), então o
# Streamlit sobe direto.

exec "$@"
