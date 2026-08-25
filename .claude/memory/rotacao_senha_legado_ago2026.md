---
name: rotacao-senha-legado-ago2026
description: "Incidente real: app quebrou (Não foi possível conectar ao banco) após rotação da senha do postgres nativo do sga legado em 05/08/2026 — app usa DB_HOST=host-postgres/DB_USER=postgres direto, fora do padrão Django, não mapeado na varredura inicial"
metadata:
  node_type: memory
  type: project
  originSessionId: session_01LWwXEKicVtyv8davwHFau9
  modified: 2026-08-25T13:03:27.021Z
---

Em 05/08/2026, a senha do superusuário `postgres` do Postgres **nativo** da VPS (banco `sga`, o legado monolítico) foi rotacionada pelo guarda-chuva `multi-aplicacao` (ver `rotacao_credenciais_vps_agosto2026.md` lá para o histórico completo).

**Incidente real:** `relatorios` (app **Streamlit**, não Django) conecta direto nesse Postgres — `DB_HOST=host-postgres` (gateway Docker para o host, `172.17.0.1`), `DB_USER=postgres`, `DB_NAME=sga`, `.env` plano via `env_file` (sem Docker Secret). Como não segue o padrão de variável Django (`DATABASE_PASSWORD`/`LEGADO_DB_PASSWORD`), **não foi pego pela varredura inicial da rotação** — só foi descoberto porque o usuário reportou a app fora do ar (`repository.py::_conectar_com_retry`, erro "Não foi possível conectar ao banco de dados"). Corrigido: `.env` (`DB_PASSWORD`) atualizado + `docker stack deploy -c stack.yml relatorios` (editar só o `.env` não é suficiente — `docker service update` não relê `env_file`). Validado com `psycopg2.connect()` real dentro do container novo.

**Why:** apps fora do padrão Django/Swarm-secret (Streamlit, scripts standalone) são um ponto cego real em rotações de credencial — precisam de varredura por host/usuário, não por nome de variável.

**How to apply:** numa próxima rotação da senha do `postgres` legado, sempre incluir este app na lista de consumidores a atualizar (`DB_PASSWORD` no `.env`, seguido de `docker stack deploy`).

**Atualização 25/08/2026 (parte 1):** o `.env` **local** da Note_Oficial (usado por `manage.py shell`/desenvolvimento fora do Docker) também estava com a senha antiga — só descoberto ao tentar criar a permissão `view_campanhas` ([[projeto_dashboard_campanhas]]) via `manage.py shell` e receber `password authentication failed`. Corrigido com a senha atual (`DB_PASSWORD` no `.env` local). Confirma o ponto cego: a rotação de agosto/2026 tratou o `.env` do deploy (Docker/VPS), mas não o `.env` de desenvolvimento local — os dois arquivos são independentes (o local nunca é sincronizado a partir do de produção).

**Atualização 25/08/2026 (parte 2 — causa raiz real do login local quebrado, ~1h de diagnóstico):** corrigir o `.env` local **não resolveu o login** — o app continuava mostrando "Não foi possível conectar ao banco de dados" mesmo depois de reiniciar múltiplos processos Streamlit locais (venv porta 8001, devcontainer porta 8501) e confirmar por vários ângulos (psycopg2 direto, Django ORM, `UserRepository.get_user()` chamado direto) que a conexão via `.env` funcionava perfeitamente. **Causa real:** existe um `.streamlit/secrets.toml` (gitignored, não sincronizado por nada) com a senha antiga hardcoded desde abril/2026. `service.py::_get_db_secret()` — usado só pela camada de login (`DataService`/`UserService`, diferente do Django ORM que lê `os.environ` puro) — **prioriza `st.secrets` (secrets.toml) sobre o `.env`** sempre que o arquivo existe e `SGR_DOCKER_DEPLOY` não está setado (só setado no deploy Docker). Ou seja, o `.env` local ficou irrelevante para o login local o tempo todo — o `secrets.toml` esquecido é que mandava. Corrigido: `DB_PASSWORD` atualizado também em `.streamlit/secrets.toml`.

**Why:** numa app com múltiplas fontes de credencial (`.env` + `st.secrets` + Docker env), corrigir só uma não é suficiente — a ordem de precedência do código (`_get_db_secret`) precisa ser conhecida, não assumida. `secrets.toml` é fácil de esquecer por ser gitignored e nunca aparecer em `git status`/diffs.

**How to apply:** numa próxima rotação de senha do `postgres` legado, atualizar SEMPRE os três: `.env` de produção (deploy Docker/VPS), `.env` local de cada máquina de desenvolvimento, **e** `.streamlit/secrets.toml` local de cada máquina (se existir — rodar `find . -name secrets.toml` para achar). Se o login local falhar mesmo com `.env` corrigido e processo reiniciado, checar `.streamlit/secrets.toml` antes de suspeitar de pg_hba/infra.
